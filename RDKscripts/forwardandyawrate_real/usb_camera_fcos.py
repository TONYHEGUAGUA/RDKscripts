#!/usr/bin/env python3

################################################################################
# Copyright (c) 2024,D-Robotics.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################



import sys
import signal
import os
os.environ["DISPLAY"] = ":0"  # 在导入任何图形库之前设置
from hobot_dnn import pyeasy_dnn as dnn
from hobot_vio import libsrcampy as srcampy
import numpy as np
import cv2
import colorsys
from time import time

import ctypes
import json

from shared_vars import shared_x,shared_y,coord_lock

# ====================== WebSocket导入与全局变量定义 ======================
import asyncio
import websockets
import threading
from io import BytesIO

WS_PORT = 8765               # WebSocket端口
JPEG_QUALITY = 85            # JPEG压缩质量（1-100）
MAX_FPS = 25                 # 最大传输帧率

def signal_handler(signal, frame):
    print("\nExiting program")
    sys.exit(0)

output_tensors = None

fcos_postprocess_info = None

class hbSysMem_t(ctypes.Structure):
    _fields_ = [
        ("phyAddr",ctypes.c_double),
        ("virAddr",ctypes.c_void_p),
        ("memSize",ctypes.c_int)
    ]

class hbDNNQuantiShift_yt(ctypes.Structure):
    _fields_ = [
        ("shiftLen",ctypes.c_int),
        ("shiftData",ctypes.c_char_p)
    ]

class hbDNNQuantiScale_t(ctypes.Structure):
    _fields_ = [
        ("scaleLen",ctypes.c_int),
        ("scaleData",ctypes.POINTER(ctypes.c_float)),
        ("zeroPointLen",ctypes.c_int),
        ("zeroPointData",ctypes.c_char_p)
    ]

class hbDNNTensorShape_t(ctypes.Structure):
    _fields_ = [
        ("dimensionSize",ctypes.c_int * 8),
        ("numDimensions",ctypes.c_int)
    ]

class hbDNNTensorProperties_t(ctypes.Structure):
    _fields_ = [
        ("validShape",hbDNNTensorShape_t),
        ("alignedShape",hbDNNTensorShape_t),
        ("tensorLayout",ctypes.c_int),
        ("tensorType",ctypes.c_int),
        ("shift",hbDNNQuantiShift_yt),
        ("scale",hbDNNQuantiScale_t),
        ("quantiType",ctypes.c_int),
        ("quantizeAxis", ctypes.c_int),
        ("alignedByteSize",ctypes.c_int),
        ("stride",ctypes.c_int * 8)
    ]

class hbDNNTensor_t(ctypes.Structure):
    _fields_ = [
        ("sysMem",hbSysMem_t * 4),
        ("properties",hbDNNTensorProperties_t)
    ]


class FcosPostProcessInfo_t(ctypes.Structure):
    _fields_ = [
        ("height",ctypes.c_int),
        ("width",ctypes.c_int),
        ("ori_height",ctypes.c_int),
        ("ori_width",ctypes.c_int),
        ("score_threshold",ctypes.c_float),
        ("nms_threshold",ctypes.c_float),
        ("nms_top_k",ctypes.c_int),
        ("is_pad_resize",ctypes.c_int)
    ]


libpostprocess = ctypes.CDLL('/usr/lib/libpostprocess.so')

get_Postprocess_result = libpostprocess.FcosPostProcess
get_Postprocess_result.argtypes = [ctypes.POINTER(FcosPostProcessInfo_t)]
get_Postprocess_result.restype = ctypes.c_char_p

def get_TensorLayout(Layout):
    if Layout == "NCHW":
        return int(2)
    else:
        return int(0)

def limit_display_cord(coor):
    coor[0] = max(min(1920, coor[0]), 0)
    # min coor is set to 2 not 0, leaving room for string display
    coor[1] = max(min(1080, coor[1]), 2)
    coor[2] = max(min(1920, coor[2]), 0)
    coor[3] = max(min(1080, coor[3]), 0)
    return coor

# detection model class names
def get_classes():
    return np.array(["person", "bicycle", "car",
                     "motorcycle", "airplane", "bus",
                     "train", "truck", "boat",
                     "traffic light", "fire hydrant", "stop sign",
                     "parking meter", "bench", "bird",
                     "cat", "dog", "horse",
                     "sheep", "cow", "elephant",
                     "bear", "zebra", "giraffe",
                     "backpack", "umbrella", "handbag",
                     "tie", "suitcase", "frisbee",
                     "skis", "snowboard", "sports ball",
                     "kite", "baseball bat", "baseball glove",
                     "skateboard", "surfboard", "tennis racket",
                     "bottle", "wine glass", "cup",
                     "fork", "knife", "spoon",
                     "bowl", "banana", "apple",
                     "sandwich", "orange", "broccoli",
                     "carrot", "hot dog", "pizza",
                     "donut", "cake", "chair",
                     "couch", "potted plant", "bed",
                     "dining table", "toilet", "tv",
                     "laptop", "mouse", "remote",
                     "keyboard", "cell phone", "microwave",
                     "oven", "toaster", "sink",
                     "refrigerator", "book", "clock",
                     "vase", "scissors", "teddy bear",
                     "hair drier", "toothbrush"])

# bgr格式图片转换成 NV12格式
def bgr2nv12_opencv(image):
    height, width = image.shape[0], image.shape[1]
    area = height * width
    yuv420p = cv2.cvtColor(image, cv2.COLOR_BGR2YUV_I420).reshape((area * 3 // 2,))
    y = yuv420p[:area]
    uv_planar = yuv420p[area:].reshape((2, area // 4))
    uv_packed = uv_planar.transpose((1, 0)).reshape((area // 2,))

    nv12 = np.zeros_like(yuv420p)
    nv12[:height * width] = y
    nv12[height * width:] = uv_packed
    return nv12


def draw_bboxs(image, bboxes, ori_w, ori_h, target_w, target_h, classes=get_classes()):
    global person_x
    global person_y
    num_classes = len(classes)
    image_h, image_w, channel = image.shape
    hsv_tuples = [(1.0 * x / num_classes, 1., 1.) for x in range(num_classes)]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(
        map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),
            colors))

    fontScale = 0.5
    bbox_thick = int(0.6 * (image_h + image_w) / 600)

    # 计算缩放比例
    scale_x = target_w / ori_w
    scale_y = target_h / ori_h
    screen_center = (320, 240)  # 屏幕中心点

    # 存储所有 person 的坐标和距离
    person_list = []
    min_distance = float('inf')
    closest_x, closest_y = 320, 240  # 默认值

    # 第一次遍历：收集所有 person 的距离信息
    for result in bboxes:
        bbox = result['bbox']
        score = result['score']
        id = int(result['id'])
        name = result['name']
        if name != "person":
            continue  # 只处理 person 类别
        
        coor = [round(i) for i in bbox]
        # 计算缩放后中心点
        scaled_coor = [
            int(coor[0] * scale_x),
            int(coor[1] * scale_y),
            int(coor[2] * scale_x),
            int(coor[3] * scale_y)
        ]
        center_x = (scaled_coor[0] + scaled_coor[2]) / 2
        center_y = (scaled_coor[1] + scaled_coor[3]) / 2
        distance = pow(center_x - screen_center[0],2) + pow(center_y - screen_center[1],2)

        # 记录 person 信息
        person_list.append({
            "scaled_coor": scaled_coor,
            "distance": distance,
            "original_coor": coor,
            "score": score
        })

        # 更新最近 person 的坐标
        if distance < min_distance:
            min_distance = distance
            closest_x = (coor[0] + coor[2]) / 2  # 原始坐标中心（未缩放）
            closest_y = (coor[1] + coor[3]) / 2

    # 第二次遍历：绘制边界框（根据距离选择颜色）
    for person in person_list:
        scaled_coor = person["scaled_coor"]
        distance = person["distance"]
        coor = person["original_coor"]
        score = person["score"]

        # 判断是否为最近 person
        if distance == min_distance:
            bbox_color = (0, 0, 255)   # 红色框
            text_color = (255, 255, 255)  # 白色文本
        else:
            bbox_color = (0, 255, 0)   # 绿色框
            text_color = (0, 0, 255)    # 红色文本

        # 调整坐标到目标分辨率
        coor[0] = int(coor[0] * scale_x)
        coor[1] = int(coor[1] * scale_y)
        coor[2] = int(coor[2] * scale_x)
        coor[3] = int(coor[3] * scale_y)

        # 绘制边界框
        c1, c2 = (coor[0], coor[1]), (coor[2], coor[3])
        cv2.rectangle(image, c1, c2, bbox_color, bbox_thick + 2)

        # 绘制标签
        bbox_mess = f'person: {score:.2f}'
        t_size = cv2.getTextSize(bbox_mess, cv2.FONT_HERSHEY_SIMPLEX, fontScale, bbox_thick // 2)[0]
        cv2.rectangle(image, c1, (c1[0] + t_size[0], c1[1] - t_size[1] - 3), bbox_color, -1)
        cv2.putText(image, bbox_mess, (c1[0], c1[1] - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, fontScale, text_color,
                    bbox_thick // 2, lineType=cv2.LINE_AA)

    # 更新共享坐标
    with coord_lock:
        shared_x.value = int(closest_x)
        shared_y.value = int(closest_y)

    return image

def get_display_res():
    if os.path.exists("/usr/bin/get_hdmi_res") == False:
        return 1920, 1080

    import subprocess
    p = subprocess.Popen(["/usr/bin/get_hdmi_res"], stdout=subprocess.PIPE)
    result = p.communicate()
    res = result[0].split(b',')
    res[1] = max(min(int(res[1]), 1920), 0)
    res[0] = max(min(int(res[0]), 1080), 0)
    return int(res[1]), int(res[0])


def is_usb_camera(device):
    try:
        cap = cv2.VideoCapture(device)
        if not cap.isOpened():
            return False
        cap.release()
        return True
    except Exception:
        return False

def find_first_usb_camera():
    video_devices = [os.path.join('/dev', dev) for dev in os.listdir('/dev') if dev.startswith('video')]
    for dev in video_devices:
        if is_usb_camera(dev):
            return dev
    return None

def print_properties(pro):
    print("tensor type:", pro.tensor_type)
    print("data type:", pro.dtype)
    print("layout:", pro.layout)
    print("shape:", pro.shape)

# ====================== WebSocket配置部分 ======================
class WebSocketServer:
    def __init__(self):
        self.clients = set()
        self.lock = threading.Lock()
        self.last_frame = None
        
    async def handler(self, websocket):  # 正确包含两个参数
        """处理客户端连接"""
        print(websocket.request.path)
        with self.lock:
            self.clients.add(websocket)
        try:
            while True:
                if self.last_frame:
                    await websocket.send(self.last_frame)
                await asyncio.sleep(1/MAX_FPS)
        except websockets.ConnectionClosed:
            pass
        finally:
            with self.lock:
                self.clients.remove(websocket)
                
    def update_frame(self, frame):
        """更新待发送的帧数据"""
        with self.lock:
            self.last_frame = frame
            
    def start(self):
        """启动服务"""
        async def _start():
            async with websockets.serve(self.handler, "0.0.0.0", WS_PORT):
                await asyncio.Future()
        threading.Thread(target=lambda: asyncio.run(_start())).start()

def main():
    #signal.signal(signal.SIGINT, signal_handler)
    ###创建编码器
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 使用XVID编码器
    out_box = cv2.VideoWriter('output_video_boxes.avi', fourcc, 15.0, (640, 480))
    #out_fresh = cv2.VideoWriter('output_video_fresh.avi', fourcc, 30.0, (1280, 720))

    # ====================== WebSocket main部分 ======================
    # 初始化WebSocket服务
    ws_server = WebSocketServer()
    ws_server.start()
    print(f"WebSocket服务已启动,端口:{WS_PORT}")

    models = dnn.load('/app/pydev_demo/models/fcos_512x512_nv12.bin')
    # 打印输入 tensor 的属性
    print_properties(models[0].inputs[0].properties)
    # 打印输出 tensor 的属性
    print(len(models[0].outputs))
    for output in models[0].outputs:
        print_properties(output.properties)

    if len(sys.argv) > 1:
        video_device = sys.argv[1]
    else:
        video_device = find_first_usb_camera()

    if video_device is None:
        print("No USB camera found.")
        sys.exit(-1)

    print(f"Opening video device: {video_device}")
    cap = cv2.VideoCapture(video_device)
    if(not cap.isOpened()):
        exit(-1)

    print("Open usb camera successfully")
    # 设置usb camera的输出图像格式为 MJPEG， 分辨率 640 x 480
    # 可以通过 v4l2-ctl -d /dev/video8 --list-formats-ext 命令查看摄像头支持的分辨率
    # 根据应用需求调整该采集图像的分辨率
    codec = cv2.VideoWriter_fourcc( 'M', 'J', 'P', 'G' )
    cap.set(cv2.CAP_PROP_FOURCC, codec)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Get HDMI display object
    disp = srcampy.Display()
    # For the meaning of parameters, please refer to the relevant documents of HDMI display
    # disp_w, disp_h = get_display_res()
    resolution_list = disp.get_display_res()
    for res in resolution_list:
        # First, exclude 0 resolution and other invalid resolutions.
        if res[0] == 0 | res[1] == 0:
            break
        # If disp is set, it defaults to iterating to the smallest resolution for use.
        disp_w = res[0]
        disp_h = res[1]
    disp.display(0, disp_w, disp_h)

    # 获取结构体信息
    fcos_postprocess_info = FcosPostProcessInfo_t()
    fcos_postprocess_info.height = 512
    fcos_postprocess_info.width = 512
    fcos_postprocess_info.ori_height = disp_h
    fcos_postprocess_info.ori_width = disp_w
    fcos_postprocess_info.score_threshold = 0.5
    fcos_postprocess_info.nms_threshold = 0.6
    fcos_postprocess_info.nms_top_k = 5
    fcos_postprocess_info.is_pad_resize = 0

    output_tensors = (hbDNNTensor_t * len(models[0].outputs))()

    for i in range(len(models[0].outputs)):
        output_tensors[i].properties.tensorLayout = get_TensorLayout(models[0].outputs[i].properties.layout)
        #print(output_tensors[i].properties.tensorLayout)
        if (len( models[0].outputs[i].properties.scale_data) == 0):
            output_tensors[i].properties.quantiType = 0
        else:
            output_tensors[i].properties.quantiType = 2
            scale_data_tmp = models[0].outputs[i].properties.scale_data.reshape(1, 1, 1, models[0].outputs[i].properties.shape[3])
            output_tensors[i].properties.scale.scaleData = scale_data_tmp.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        for j in range(len(models[0].outputs[i].properties.shape)):
            output_tensors[i].properties.validShape.dimensionSize[j] = models[0].outputs[i].properties.shape[j]
            output_tensors[i].properties.alignedShape.dimensionSize[j] = models[0].outputs[i].properties.shape[j]

    start_time = time()
    image_counter = 0
    while True:
        _ ,frame = cap.read()
        #out_fresh.write(frame)
        # print(frame.shape)

        if frame is None:
            print("Failed to get image from usb camera")
        # 把图片缩放到模型的输入尺寸
        # 获取算法模型的输入tensor 的尺寸
        h, w = models[0].inputs[0].properties.shape[2], models[0].inputs[0].properties.shape[3]
        des_dim = (w, h)
        resized_data = cv2.resize(frame, des_dim, interpolation=cv2.INTER_AREA)

        nv12_data = bgr2nv12_opencv(resized_data)

        t0 = time()
        # Forward
        outputs = models[0].forward(nv12_data)
        t1 = time()
        # print("forward time is :", (t1 - t0))

        # Do post process
        strides = [8, 16, 32, 64, 128]
        for i in range(len(strides)):
            if (output_tensors[i].properties.quantiType == 0):
                output_tensors[i].sysMem[0].virAddr = ctypes.cast(outputs[i].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), ctypes.c_void_p)
                output_tensors[i + 5].sysMem[0].virAddr = ctypes.cast(outputs[i + 5].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), ctypes.c_void_p)
                output_tensors[i + 10].sysMem[0].virAddr = ctypes.cast(outputs[i + 10].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), ctypes.c_void_p)
            else:
                output_tensors[i].sysMem[0].virAddr = ctypes.cast(outputs[i].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)), ctypes.c_void_p)
                output_tensors[i + 5].sysMem[0].virAddr = ctypes.cast(outputs[i + 5].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)), ctypes.c_void_p)
                output_tensors[i + 10].sysMem[0].virAddr = ctypes.cast(outputs[i + 10].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)), ctypes.c_void_p)

            libpostprocess.FcosdoProcess(output_tensors[i], output_tensors[i + 5], output_tensors[i + 10], ctypes.pointer(fcos_postprocess_info), i)

        result_str = get_Postprocess_result(ctypes.pointer(fcos_postprocess_info))
        result_str = result_str.decode('utf-8')
        t2 = time()
        # print("FcosdoProcess time is :", (t2 - t1))
        # print(result_str)

        # draw result
        # 解析JSON字符串
        data = json.loads(result_str[14:])

        if frame.shape[0]!=disp_h or frame.shape[1]!=disp_w:
            frame = cv2.resize(frame, (disp_w,disp_h), interpolation=cv2.INTER_AREA)

        # Draw bboxs
        # box_bgr = draw_bboxs(frame, data)
        box_bgr = draw_bboxs(frame, data, fcos_postprocess_info.width, fcos_postprocess_info.height, disp_w, disp_h)

        # ====================== WebSocket main部分 ======================
        # draw result
        # 解析JSON字符串
        data = json.loads(result_str[14:])

        if frame.shape[0]!=disp_h or frame.shape[1]!=disp_w:
            frame = cv2.resize(frame, (disp_w,disp_h), interpolation=cv2.INTER_AREA)

        # Draw bboxs
        # box_bgr = draw_bboxs(frame, data)
        box_bgr = draw_bboxs(frame, data, fcos_postprocess_info.width, fcos_postprocess_info.height, disp_w, disp_h)

        out_box.write(box_bgr)  # 写入帧到输出文件

        # WebSocket转换并发送JPEG帧
        _, jpeg = cv2.imencode('.jpg', box_bgr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        ws_server.update_frame(jpeg.tobytes())

        
        # cv2.imwrite("imf.jpg", box_bgr)
        #cv2.imshow('frame',box_bgr)
        #cv2.waitKey(1)
        # Convert to nv12 for HDMI display
        box_nv12 = bgr2nv12_opencv(box_bgr)
        disp.set_img(box_nv12.tobytes())

        finish_time = time()
        image_counter += 1
        if finish_time - start_time >  10:
            print(start_time, finish_time, image_counter)
            print("FPS: {:.2f}".format(image_counter / (finish_time - start_time)))
            start_time = finish_time
            image_counter = 0

if __name__ == "__main__":
    main()