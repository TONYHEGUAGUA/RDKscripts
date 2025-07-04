from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
from dronekit import connect, VehicleMode
import time
from pymavlink import mavutil 
from shared_vars import shared_x, shared_y, data_lock

from dronecommands import setPositionTarget
#yaw相关的值都使用角度值
yawrate_max = 30
person_mid = 256
person_x = 256
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


vehicle = connect('/dev/ttyUSB0', wait_ready=True)
print("drone connected")
time.sleep(1)
arm_and_takeoff(5)
print("reached 5 meters")
time.sleep(1)
print("start to track")
while(1):
    with data_lock:
        person_x = shared_x.value
        person_y = shared_y.value
    yawrate = (person_x - person_mid)*yawrate_max/person_mid
    setPositionTarget(vehicle,(0,0),yawrate)
    time.sleep(0.1)