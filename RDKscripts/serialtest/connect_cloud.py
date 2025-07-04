import serial
import time

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

def send_at_connect():
    send_at_command("AT")
    send_at_command("ATI")
    send_at_command("AT+MIPCALL=1")
    send_at_command("AT+MIPCALL?")
    send_at_command('AT+HMCON=0,60,"47e7207a2f.st1.iotda-device.cn-north-4.myhuaweicloud.com","1883","686544a6d582f20018375e4d_mode","Qyc2946782800",0')
    send_at_command('AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",60,"{\\"services\\":[{\\"service_id\\":\\"mode\\",\\"properties\\":{\\"mode\\":1}}]}"')
    

send_at_connect()