from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
from typing import Tuple
from pymavlink import mavutil
from dronekit import Vehicle
import math

def setYaw(vehicle: Vehicle, relativeYaw: float) -> None:
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,
        0, #confirmation
        abs(relativeYaw),    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1 if relativeYaw >= 0 else -1, # param 3, direction -1 ccw, 1 cw
        1, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used

    vehicle.send_mavlink(msg)
    vehicle.flush()

def setPositionTarget(vehicle: Vehicle, position: Tuple[float, float], yawRate: float) -> None:
    localNorth, localEast = position
    # Find altitude target for NED frame
    ignoreVelocityMask =  0b111000
    ignoreAccelMask =  0b111000000
    ignoreYaw = 0b10000000000
    emptyMask = 0b0000000000000000
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, # Use offset from current position
        emptyMask + ignoreAccelMask + ignoreVelocityMask + ignoreYaw, # type_mask
        localNorth, localEast, 0,
        0, 0, 0, # x, y, z velocity in m/s (not used)
        0, 0, 0, # x, y, z acceleration (not used)
        0, math.radians(yawRate))    # yaw, yaw_rate

    vehicle.send_mavlink(msg)