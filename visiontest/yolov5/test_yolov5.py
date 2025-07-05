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

import numpy as np
import cv2
from hobot_dnn import pyeasy_dnn as dnn
import time
import ctypes
import json 
import sys
import os
os.environ["DISPLAY"] = ":0"  # 在导入任何图形库之前设置


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


class Yolov5PostProcessInfo_t(ctypes.Structure):
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

get_Postprocess_result = libpostprocess.Yolov5PostProcess
get_Postprocess_result.argtypes = [ctypes.POINTER(Yolov5PostProcessInfo_t)]  
get_Postprocess_result.restype = ctypes.c_char_p  

def get_TensorLayout(Layout):
    if Layout == "NCHW":
        return int(2)
    else:
        return int(0)


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


def get_hw(pro):
    if pro.layout == "NCHW":
        return pro.shape[2], pro.shape[3]
    else:
        return pro.shape[1], pro.shape[2]

def is_usb_camera(device):
    try:
        cap = cv2.VideoCapture(device)
        if not cap.isOpened():
            return False
        cap.release()
        return True
    except Exception:
        return False

def print_properties(pro):
    print("tensor type:", pro.tensor_type)
    print("data type:", pro.dtype)
    print("layout:", pro.layout)
    print("shape:", pro.shape)

def find_first_usb_camera():
    video_devices = [os.path.join('/dev', dev) for dev in os.listdir('/dev') if dev.startswith('video')]
    for dev in video_devices:
        if is_usb_camera(dev):
            return dev
    return None


# ... 前面的导入和类定义保持不变 ...

if __name__ == '__main__':
    # 1. 初始化摄像头
    if len(sys.argv) > 1:
        video_device = sys.argv[1]
    else:
        video_device = find_first_usb_camera()

    if video_device is None:
        print("No USB camera found.")
        sys.exit(-1)

    print(f"Opening video device: {video_device}")
    cap = cv2.VideoCapture(video_device)
    if not cap.isOpened():
        raise IOError("无法打开USB摄像头")  # 摄像头检查[12](@ref)
    
    # 获取原始摄像头分辨率
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 2. 加载模型
    
    models = dnn.load('/app/pydev_demo/models/yolov5s_672x672_nv12.bin')
    print_properties(models[0].inputs[0].properties)
    # 打印输出 tensor 的属性
    print(len(models[0].outputs))
    for output in models[0].outputs:
        print_properties(output.properties)
    h, w = get_hw(models[0].inputs[0].properties)
    des_dim = (w, h)  # 模型要求的672x672尺寸[1](@ref)
    
    # 3. 视频处理循环
    while True:
        ret, frame = cap.read()
        if ret:  
            cv2.imwrite("raw_frame.jpg", frame)  # 检查原始帧是否正常 
        if not ret:
            print("无法获取视频帧")
            break
        
        # 4. 实时预处理
        resized_data = cv2.resize(frame, des_dim, interpolation=cv2.INTER_AREA)
        nv12_data = bgr2nv12_opencv(resized_data)
        cv2.imwrite("frame_after_resize.jpg", frame)
        # 5. 模型推理
        outputs = models[0].forward(nv12_data)
        
        # 6. 后处理设置
        yolov5_postprocess_info = Yolov5PostProcessInfo_t()
        yolov5_postprocess_info.height = h
        yolov5_postprocess_info.width = w
        yolov5_postprocess_info.ori_height = original_height
        yolov5_postprocess_info.ori_width = original_width
        yolov5_postprocess_info.score_threshold = 0.4
        yolov5_postprocess_info.nms_threshold = 0.45
        yolov5_postprocess_info.nms_top_k = 20
        yolov5_postprocess_info.is_pad_resize = 0
        
        # 7. 后处理执行
        output_tensors = (hbDNNTensor_t * len(models[0].outputs))()
        for i in range(len(models[0].outputs)):
            output_tensors[i].properties.tensorLayout = get_TensorLayout(outputs[i].properties.layout)
            # print(output_tensors[i].properties.tensorLayout)
            if (len(outputs[i].properties.scale_data) == 0):
                output_tensors[i].properties.quantiType = 0
                output_tensors[i].sysMem[0].virAddr = ctypes.cast(outputs[i].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), ctypes.c_void_p)
            else:
                output_tensors[i].properties.quantiType = 2       
                output_tensors[i].properties.scale.scaleData = outputs[i].properties.scale_data.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                output_tensors[i].sysMem[0].virAddr = ctypes.cast(outputs[i].buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)), ctypes.c_void_p)
            
            for j in range(len(outputs[i].properties.shape)):
                output_tensors[i].properties.validShape.dimensionSize[j] = outputs[i].properties.shape[j]
                # ... 后处理设置保持不变 ...
            libpostprocess.Yolov5doProcess(output_tensors[i], ctypes.pointer(yolov5_postprocess_info), i)
        
        # 8. 解析结果
        result_str = get_Postprocess_result(ctypes.pointer(yolov5_postprocess_info))
        result_str = result_str.decode('utf-8')
        data = json.loads(result_str[16:])
        #print(data)
        # 9. 实时绘制结果
        for result in data:
            bbox = result['bbox']
            score = result['score']
            name = result['name']
            id = result['id']  # id  
            # 打印信息  
            print(f"bbox: {bbox}, score: {score}, id: {id}, name: {name}")
            # 将归一化坐标转换为原始分辨率坐标
            x1 = int(bbox[0])
            y1 = int(bbox[1])
            x2 = int(bbox[2])
            y2 = int(bbox[3])
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            font = cv2.FONT_HERSHEY_SIMPLEX  
            cv2.putText(frame, f'{name} {score:.2f}', (x1, y1 - 10),
                       font, 0.5, (0, 255, 0), 1)
        
        # 10. 实时显示
        cv2.imshow('YOLOv5 Real-time Detection', frame)
        cv2.waitKey(0)
    # 11. 释放资源
    cap.release()
    cv2.destroyAllWindows()

