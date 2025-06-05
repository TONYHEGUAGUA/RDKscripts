from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
from dronekit import connect, VehicleMode
import time
from pymavlink import mavutil 

from dronecommands import *
from shared_vars import shared_x,shared_y,coord_lock
person_mid = 256


def main():
    vehicle = connect('/dev/ttyS1', wait_ready=True,baud=921600,rate=30) #成功通过导线直接连接飞控串口3
    print("drone connected")
    time.sleep(1)
    start_position = vehicle.location.global_relative_frame
    arm_and_takeoff(vehicle,5)
    print("reached 5 meters")
    time.sleep(1)
    print("send yaw condition cmd")
    time.sleep(1)
    print("start to track in forward")

    while(1):
        if not(vehicle.mode == VehicleMode("GUIDED")):
            break;
        with coord_lock:
            person_x = shared_x.value
            person_y = shared_y.value
        foward_speed = 0
        yaw_rate = 0
        print("person_y = ",person_y)
        if person_y - person_mid>30:
            foward_speed = -0.5
        if person_y - person_mid<-30:
            foward_speed = 0.5
        if person_x - person_mid>30:
            yaw_rate = 0.174
        if person_x - person_mid<-30:
            yaw_rate = -0.174

        print("foward_speed = ",foward_speed)
        print("yaw_rate = ",yaw_rate)
        send_body_velocity_yaw_rate(vehicle,foward_speed,0,0,yaw_rate)
        time.sleep(0.1)

if __name__ == "__main__":
    main()