import cv2

# 创建摄像头对象，0表示默认摄像头（/dev/video0）
cap = cv2.VideoCapture(0)

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 设置窗口名称（可选）
window_name = 'Camera Preview'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

try:
    while True:
        # 逐帧捕获
        print("1")
        ret, frame = cap.read()
        
        # 显示帧
        cv2.imshow(window_name, frame)
        
        # 按ESC或q键退出（1毫秒延迟，确保图像更新）
        key = cv2.waitKey(1)
        if key == 27 or key == ord('q'):
            print("用户退出")
            break

finally:
    # 释放资源并关闭窗口
    cap.release()
    cv2.destroyAllWindows()