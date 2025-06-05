from drone_forward_yawrate import main as fly_main
from usb_camera_fcos import main as vision_main
import threading
t1 = threading.Thread(target=fly_main)
t2 = threading.Thread(target=vision_main)
t1.start()
t2.start()
t1.join()
t2.join()