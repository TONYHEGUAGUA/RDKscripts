#!/usr/bin/env python3
import cv2
import time
import os
os.environ["DISPLAY"] = ":0"  # 在导入任何图形库之前设置
# 初始化摄像头 - 默认使用/dev/video0[1,3,5](@ref)
cap = cv2.VideoCapture(0)

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开USB摄像头！请检查：")
    print("1. 摄像头是否连接正确（ls /dev/video*）[1](@ref)")
    print("2. 用户权限（sudo usermod -aG video $USER）[6](@ref)")
    exit()

# 设置摄像头参数（可选）
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # 宽度
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 高度
cap.set(cv2.CAP_PROP_FPS, 30)           # 帧率

# 获取实际分辨率用于视频保存
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 创建视频编码器（FourCC）[2,6](@ref)
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 可选：MJPG, X264, DIVX
# fourcc = cv2.VideoWriter_fourcc('M','J','P','G')  # 另一种写法

# 生成带时间戳的文件名
timestamp = time.strftime("%Y%m%d_%H%M%S")
output_file = f'usb_camera_{timestamp}.avi'

# 创建VideoWriter对象[2](@ref)
out = cv2.VideoWriter(
    output_file,
    fourcc,
    20.0,  # 帧率（FPS）
    (frame_width, frame_height)  # 分辨率
)


while cap.isOpened():
    # 读取摄像头帧
    #print("正在录制")
    ret, frame = cap.read()
        
    if not ret:
        print("无法获取视频帧，可能摄像头已断开")
        break
        
    # 写入视频文件
    out.write(frame)
        
    # 显示预览画面（可选）
    cv2.imshow('USB Camera Recording', frame)