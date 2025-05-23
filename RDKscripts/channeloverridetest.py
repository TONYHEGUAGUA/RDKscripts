from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
from dronekit import connect
import time
# Connect to the Vehicle (in this case a UDP endpoint)
#vehicle = connect('/dev/ttyUSB0', wait_ready=True, baud=921600)
#vehicle = connect('/dev/ttyACM0', wait_ready=True, baud=57600)
#vehicle = connect('/dev/ttyUSB0', wait_ready=True, baud=57600) #降低波特率后成功

vehicle = connect('/dev/ttyS1', wait_ready=True,baud=57600) #成功通过导线直接连接飞控串口4
print("drone connected")

# while(1):
#     #override channel7
#     vehicle.channels.overrides = {'7':1100}
#     time.sleep(1)
#     vehicle.channels.overrides = {'7':1500}
#     time.sleep(1)
#     vehicle.channels.overrides = {'7':1900}
#     time.sleep(1)
while(1):
        for pwm_num in range(1100, 1901):  # 1901确保包含1900
                vehicle.channels.overrides = {'7':pwm_num}
                time.sleep(0.01)
        for pwm_num in range(1100, 1991):  # 1901确保包含1900
                vehicle.channels.overrides = {'7':3000-pwm_num}
                time.sleep(0.01)