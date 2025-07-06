from collections import abc
import collections
collections.MutableMapping = abc.MutableMapping
from dronekit import connect, VehicleMode


import serial
import time
import json

vehicle = None
mode_now = None
mode_before = None

##################连接飞控#######################
def connect_ardupilot():
    print("in connecting MC flight controller")
    global vehicle 
    vehicle = connect('/dev/ttyS1', wait_ready=True,baud=921600,rate=30) #成功通过导线直接连接飞控串口3
    print("drone connected")
    print("Autopilot Firmware version: %s" % vehicle.version)

##################AT指令发送#######################
def send_at_command(command):
    ser.write((command + '\r\n').encode())  # 发送命令并添加回车换行符
    time.sleep(0.1)  # 等待一些时间以接收响应（视情况而定）
    response = ser.read(ser.in_waiting).decode()  # 读取响应
    return response.strip()  # 返回清理后的响应字符串

ser = serial.Serial(
    port='/dev/ttyUSB0',        # 替换为你的端口，例如 'COM3'（Windows）或 '/dev/ttyUSB0'（Linux/Mac）
    baudrate=115200,      # 设置波特率
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1           # 设置超时时间
)

#发送用于连接，分配ip，订阅服务
def send_at_connect():
    send_at_command("AT")
    send_at_command("ATI")
    send_at_command("AT+MIPCALL=1")
    send_at_command("AT+MIPCALL?")
    send_at_command('AT+HMCON=0,60,"47e7207a2f.st1.iotda-device.cn-north-4.myhuaweicloud.com","1883","686544a6d582f20018375e4d_mode","Qyc2946782800",0')
    send_at_command('AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",60,"{\\"services\\":[{\\"service_id\\":\\"mode\\",\\"properties\\":{\\"mode\\":1}}]}"')

#将模式转成数字 guided:1 land:0 loiter:2 stabilize:3 
def mode_to_number(modename):
    if modename == "STABILIZE":
        return 3 
    if modename == "LOITER":
        return 2 
    if modename == "LAND":
        return 0 
    if modename == "GUIDED":
        return 1
    return -1

def number_to_mode(modenumber):
    if modenumber == 3:
        return "STABILIZE"
    if modenumber == 2:
        return "LOITER"
    if modenumber == 0:
        return "LAND"
    if modenumber == 1:
        return "GUIDED"
    return "failed to change number to mode"



def parse_hmrec_message(raw_data):
    """解析+HMREC格式消息"""
    try:
        # 提取JSON部分（从第一个{到最后一个}）
        json_start = raw_data.find('{')
        json_end = raw_data.rfind('}') + 1
        json_str = raw_data[json_start:json_end]
        
        # 解析JSON
        data = json.loads(json_str)
        service_id = data.get("service_id", "")
        command_name = data.get("command_name", "")
        paras = data.get("paras", {})
        
        return service_id, command_name, paras
    except (json.JSONDecodeError, KeyError) as e:
        print(f"解析失败: {e}")
        return None, None, None
    

def execute_command(service_id, paras):
    global vehicle
    """根据解析结果执行控制逻辑"""
    if service_id == "mode":
        mode_value = paras.get("Mode")
        if mode_value == 0:
            #activate_land_mode()
            print("mode = %s" % number_to_mode(mode_value))
        elif mode_value == 1:
            #activate_guided_mode()
            print("mode = %s" % number_to_mode(mode_value))
        elif mode_value == 2:
            #activate_loiter_mode()
            print("mode = %s" % number_to_mode(mode_value))
        elif mode_value == 3:
            #activate_stabilize_mode()
            print("mode = %s" % number_to_mode(mode_value))
        vehicle.mode    = VehicleMode(number_to_mode(mode_value))
        #mode_data_to_send = f'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",60,"{{\\"services\\":[{{\\"service_id\\":\\"mode\\",\\"properties\\":{{\\"mode\\":{mode_value}}}}}]}}"'
        #send_at_command(mode_data_to_send)
    elif service_id == "mission":
        mission_value = paras.get("MissionControl")
        if mission_value == 1:
            #activate_gps_tracking()
            print("111")
        elif mission_value == 2:
            #activate_visual_tracking()
            print("222")
        mission_data_to_send = f'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",66,"{{\\"services\\":[{{\\"service_id\\":\\"mission\\",\\"properties\\":{{\\"mission\\":{mission_value}}}}}]}}"'
        send_at_command(mission_data_to_send)
#循环
def loop():
    global mode_now
    global mode_before
    mode_now = vehicle.mode
    if not(mode_now == mode_before):
        mode_data_to_send = f'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",60,"{{\\"services\\":[{{\\"service_id\\":\\"mode\\",\\"properties\\":{{\\"mode\\":{mode_to_number(mode_now)}}}}}]}}"'
        send_at_command(mode_data_to_send)
        print("mode change")

    #print("Mode: %s" % vehicle.mode.name)
    #print("Modenumber: %d" % mode_to_number(vehicle.mode.name))
    #print("Battery: %s" % vehicle.battery)
    #print(round(vehicle.battery.voltage, 2))

    ###AT发送模式
    #mode_data_to_send = f'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",60,"{{\\"services\\":[{{\\"service_id\\":\\"mode\\",\\"properties\\":{{\\"mode\\":{mode_to_number(vehicle.mode.name)}}}}}]}}"'
    #send_at_command(mode_data_to_send)

    ###AT发送当前任务
    #mission_type = 2
    #mission_data_to_send = f'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",66,"{{\\"services\\":[{{\\"service_id\\":\\"mission\\",\\"properties\\":{{\\"mission\\":{mission_type}}}}}]}}"'
    #send_at_command(mission_data_to_send)

    ###AT发送电池
    Battery_data_to_send = f'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",70,"{{\\"services\\":[{{\\"service_id\\":\\"Battery\\",\\"properties\\":{{\\"Battery\\":{round(vehicle.battery.voltage, 2)}}}}}]}}"'
    #send_at_command(Battery_data_to_send)

    raw_data = ser.readline().decode().strip()
    if raw_data.startswith("+HMREC"):
        service_id, _, paras = parse_hmrec_message(raw_data)
        if service_id:
            execute_command(service_id, paras)
    mode_before = mode_now
    time.sleep(0.1)

send_at_connect()
connect_ardupilot()
while(1):
    loop()