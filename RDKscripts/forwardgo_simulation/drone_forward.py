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
    vehicle = connect('udp:0.0.0.0:14550', wait_ready=True)
    print("drone connected")
    time.sleep(1)
    start_position = vehicle.location.global_relative_frame
    condition_yaw(vehicle,0,True)
    arm_and_takeoff(vehicle,5)
    print("reached 5 meters")
    time.sleep(1)
    print("start to track in forward")

    while(1):
        with coord_lock:
            person_x = shared_x.value
            person_y = shared_y.value
        foward_speed = 0
        print("person_y = ",person_y)
        if person_y - person_mid>30:
            foward_speed = -0.5
        if person_y - person_mid<-30:
            foward_speed = 0.5

        print("foward_speed = ",foward_speed)
        send_ned_velocity(vehicle,foward_speed,0,0)
        time.sleep(0.1)

if __name__ == "__main__":
    main()