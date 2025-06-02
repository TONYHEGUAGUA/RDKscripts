from dronekit import connect, VehicleMode
import time
from pymavlink import mavutil 

#mavlink消息需要至少每秒发送一次
def send_ned_yaw_rate(yaw_rate):
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
    0,       # time_boot_ms (not used)
    0, 0,    # target_system, target_component
    mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame=1
    1479,  # type_mask=1479（忽略位置/加速度/偏航，启用速度/偏航率） 0b10111000111 使用速度+角速度
    0, 0, 0,          # x/y/z位置（被忽略）
    0, 0, 0,          # vx/vy/vz速度（未使用，但type_mask启用了速度字段）
    0, 0, 0,          # afx/afy/afz加速度（被忽略）
    0, yaw_rate          # yaw（被忽略）、yaw_rate=0.174 rad/s
    )
    vehicle.send_mavlink(msg)

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
arm_and_takeoff(5)
print("Start to change yaw_rate to 10deg/s")
time.sleep(1)
for x in range(0,34):
    if not(vehicle.mode == VehicleMode("GUIDED")):
        break;
    send_ned_yaw_rate(0.174)
    time.sleep(1)
#vehicle.mode = VehicleMode("LOITER")