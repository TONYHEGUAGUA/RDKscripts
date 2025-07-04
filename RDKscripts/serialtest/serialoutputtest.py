import serial
import time

# 配置串口参数
ser = serial.Serial(
    port='/dev/ttyUSB0',    # 设备路径，根据实际修改
    baudrate=115200,        # 指定波特率115200[9,10,11](@ref)
    bytesize=serial.EIGHTBITS,  # 数据位（8位）
    parity=serial.PARITY_NONE,  # 无校验
    stopbits=serial.STOPBITS_ONE, # 停止位（1位）
    timeout=1               # 超时时间（秒）
)

try:
    if ser.is_open:
        print("串口已打开，波特率：115200")
        while True:
            # 发送数据
            data_to_send = 'AT+HMPUB=1,"$oc/devices/686544a6d582f20018375e4d_mode/sys/properties/report",60,"{\\"services\\":[{\\"service_id\\":\\"mode\\",\\"properties\\":{\\"mode\\":1}}]}"\n'
            ser.write(data_to_send.encode('utf-8'))  # 字符串转字节流发送[1,4](@ref)
            print(f"已发送：{data_to_send.strip()}")
            
            time.sleep(1)  # 每秒发送一次
except KeyboardInterrupt:
    print("用户中断")
finally:
    ser.close()  # 关闭串口
    print("串口已关闭")