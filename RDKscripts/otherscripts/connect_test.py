from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
from dronekit import connect
import time
# Connect to the Vehicle (in this case a UDP endpoint)
#vehicle = connect('/dev/ttyUSB0', wait_ready=True, baud=921600)
#vehicle = connect('/dev/ttyACM0', wait_ready=True, baud=57600)
#vehicle = connect('/dev/ttyUSB0', wait_ready=True, baud=57600) #降低波特率后成功

vehicle = connect('/dev/ttyS1', wait_ready=True,baud=921600,rate=30,timeout=60) #成功通过导线直接连接飞控串口3
print("drone connected")
# vehicle is an instance of the Vehicle class
while(1):
	print("Autopilot Firmware version: %s" % vehicle.version)
	print("Autopilot capabilities (supports ftp): %s" % vehicle.capabilities.ftp)
	print("Global Location: %s" % vehicle.location.global_frame)
	print("Global Location (relative altitude): %s" % vehicle.location.global_relative_frame)
	print("Local Location: %s" % vehicle.location.local_frame)    # NED
	print("Attitude: %s" % vehicle.attitude)
	print("Velocity: %s" % vehicle.velocity)
	print("GPS: %s" % vehicle.gps_0)
	print("Groundspeed: %s" % vehicle.groundspeed)
	print("Airspeed: %s" % vehicle.airspeed)
	print("Gimbal status: %s" % vehicle.gimbal)
	print("Battery: %s" % vehicle.battery)
	print("EKF OK?: %s" % vehicle.ekf_ok)
	print("Last Heartbeat: %s" % vehicle.last_heartbeat)
	print("Rangefinder: %s" % vehicle.rangefinder)
	print("Rangefinder distance: %s" % vehicle.rangefinder.distance)
	print("Rangefinder voltage: %s" % vehicle.rangefinder.voltage)
	print("Heading: %s" % vehicle.heading)
	print("Is Armable?: %s" % vehicle.is_armable)
	print("System status: %s" % vehicle.system_status.state)
	print("Mode: %s" % vehicle.mode.name)    # settable
	print("Armed: %s" % vehicle.armed)    # settable
	time.sleep(1)