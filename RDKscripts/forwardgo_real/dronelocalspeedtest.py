

#it can let drone fly in 0.5m/s to the left permantly

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil 
from dronecommands import *
def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print("Basic pre-arm checks")
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode    = VehicleMode("GUIDED")
    vehicle.armed   = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        if not(vehicle.mode == VehicleMode("GUIDED")):
            break;
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        #Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print("Reached target altitude")
            break
        time.sleep(1)


vehicle = connect('/dev/ttyS1', wait_ready=True,baud=921600,rate=30) #成功通过导线直接连接飞控串口3
print("drone connected")
time.sleep(1)

forward_speed = 0.5
left_speed = 0.5  # 设置向左飞行速度为0.5m/s
flight_time = 2    # 飞行时间4秒（0.5m/s × 4s = 2米）

# 获取起始位置
start_position = vehicle.location.global_relative_frame


arm_and_takeoff(5)

time.sleep(1)
print("going forward")
#condition_yaw(vehicle,0,False)
for x in range(0,5):
        send_body_velocity(vehicle,0.5,0,0)
        time.sleep(1)
    #loop
#while(1):
#	vehicle.send_mavlink(msg)
#	#vehicle.flush()
#	print("in flying")
