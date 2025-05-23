#!/usr/bin/env python3
import cv2
import asyncio
import websockets
import numpy as np

# WebSocket配置
WS_PORT = 8765          # 服务端口
CAMERA_INDEX = 0        # 默认摄像头设备号（/dev/video0）
FRAME_WIDTH = 640       # 图像宽度
FRAME_HEIGHT = 480      # 图像高度
JPEG_QUALITY = 80       # 压缩质量（0-100）

async def video_stream(websocket):
    """视频流处理协程"""
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    try:
        while cap.isOpened():
            # 读取摄像头帧
            ret, frame = cap.read()
            if not ret:
                break

            # 转换为JPEG字节流
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            
            # 发送到客户端
            await websocket.send(jpeg.tobytes())
            
            # 控制帧率（约25fps）
            await asyncio.sleep(0.04)
            
    except websockets.exceptions.ConnectionClosed:
        print("客户端断开连接")
    finally:
        cap.release()

async def main():
    """启动WebSocket服务"""
    async with websockets.serve(video_stream, "0.0.0.0", WS_PORT):
        print(f"服务已启动，可通过 ws://[你的IP]:{WS_PORT} 访问")
        await asyncio.Future()  # 永久运行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("服务已关闭")