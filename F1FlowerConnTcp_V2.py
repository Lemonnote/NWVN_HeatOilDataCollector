from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import threading
import time
import struct
import binascii

def hex_to_float(hex_str):
    """將十六進位字串轉換為 IEEE 754 單精度浮點數"""
    if len(hex_str) != 8:
        raise ValueError("十六進位字串長度不正確，應為8位")
    return struct.unpack('>f', bytes.fromhex(hex_str))[0]

def parse_response_data(response_bytes):
    """解析回應數據中的 IEEE 754 單精度浮點數"""
    hex_data = binascii.hexlify(response_bytes).decode()
    print(f"接收到的十六進位數據: {hex_data}")

    # 提取數據，這裡假設數據格式固定為兩個寄存器
    if len(hex_data) >= 16:  # 兩個寄存器，每個寄存器2字節，共4字節
        data_hex = hex_data[6:14]  # 提取第7到第14位的數據
        try:
            float_value = hex_to_float(data_hex)
            print(f"解碼得到的浮點數: {float_value}")
        except ValueError as ve:
            print(f"解碼錯誤: {ve}")
    else:
        print("接收到的數據長度不符合要求")

def send_request(client):
    """定時發送 Modbus 請求"""
    while True:
        try:
            # 讀取保持寄存器範圍 0x0007 到 0x0008
            request_address = 0x0007
            register_count = 2  # 讀取兩個寄存器
            response = client.read_holding_registers(request_address, register_count, unit=1)
            
            if response.isError():
                print(f"Modbus 錯誤: {response}")
            else:
                response_bytes = response.encode()  # 將 Modbus 回應轉為位元組流
                parse_response_data(response_bytes)
            
            time.sleep(60)  # 定時發送間隔（例如每60秒）
        except Exception as e:
            print(f"發送請求時發生錯誤: {e}")

def read_response(client):
    """持續讀取 Modbus 回應"""
    try:
        while True:
            response_bytes = client.socket.recv(4096)  # 接收數據
            if not response_bytes:
                print("未接收到數據")
                continue
            
            parse_response_data(response_bytes)
        request_received.clear()  # 重置通知狀態
    except Exception as e:
        print(f"讀取回應時發生錯誤: {e}")

def main(ip, port):
    # 創建 Modbus TCP 客戶端
    client = ModbusTcpClient(ip, port, timeout=70)  # 增加超時時間

    try:
        if client.connect():
            print("成功連接。")

            # 創建線程來發送請求和讀取回應
            send_thread = threading.Thread(target=send_request, args=(client,))
            read_thread = threading.Thread(target=read_response, args=(client,))

            # 啟動線程
            send_thread.start()
            read_thread.start()

            # 等待線程完成
            send_thread.join()
            read_thread.join()
        else:
            print("連接失敗。")

    except ModbusException as e:
        print(f"Modbus 異常: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        # 斷開連接
        client.close()

# 用法示例
#ip_address = '192.168.24.19'  # 替換為你的 Modbus TCP 伺服器 IP 地址
#port_number = 10123           # 替換為你的端口號

# 嘗試發送請求並讀取數據
#main(ip_address, port_number)


def test_modbus_request(ip, port):
    client = ModbusTcpClient(ip, port)
    
    try:
        if client.connect():
            print("成功連接。")
            
            # 發送請求數據
            request_bytes = bytes.fromhex('01 03 00 13 00 02')
            client.socket.send(request_bytes)
            
            # 接收回應數據
            response_bytes = client.socket.recv(1024)
            if response_bytes:
                hex_data = binascii.hexlify(response_bytes).decode()
                print(f"接收到的十六進位數據: {hex_data}")
                
                # 驗證回應的正確性
                if len(response_bytes) >= 7:
                    # 提取第 7 到第 14 字節的數據（注意 Python 索引從 0 開始）
                    # 需要提取的範圍是從第 6 個字節到第 14 個字節（不包括第 14 個字節）
                    data_hex = hex_data[6*2:14*2]  # 每個字節用兩個十六進位字符表示
                    print(f"提取的數據: {data_hex}")

                    # 如果需要將數據轉換為浮點數或其他格式，請根據實際數據格式進行處理
                else:
                    print("回應數據長度不符合要求。")
            else:
                print("未接收到數據。")
    
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        client.close()

from pymodbus.client.tcp import ModbusTcpClient
import binascii
import struct

def calculate_crc(data):
    """计算 CRC-16 校验码"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def create_request(start_address, quantity):
    """创建 Modbus 读取请求"""
    # 请求数据格式：功能码 0x03 + 起始地址 + 寄存器数量 + CRC 校验
    request = struct.pack('>B', 0x03)  # 功能码
    request += struct.pack('>H', start_address)  # 起始寄存器地址
    request += struct.pack('>H', quantity)  # 寄存器数量
    crc = calculate_crc(request)
    request += crc  # 附加 CRC 校验码
    return request

def test_modbus_request(ip, port):
    client = ModbusTcpClient(ip, port)
    
    try:
        if client.connect():
            print("成功連接。")
            
            # 创建 Modbus 读取请求
            start_address = 0x0008
            quantity = 14  # 读取的寄存器数量
            request_bytes = create_request(start_address, quantity)
            print(f"發送的請求: {binascii.hexlify(request_bytes).decode()}")

            # 发送请求
            client.socket.send(request_bytes)
            
            # 接收回應數據
            response_bytes = client.socket.recv(1024)
            if response_bytes:
                hex_data = binascii.hexlify(response_bytes).decode()
                print(f"接收到的十六進位數據: {hex_data}")

                # 解析数据
                if len(response_bytes) >= 7:
                    # 去除 Modbus 地址和功能码，提取数据部分
                    data_hex = hex_data[6*2:]  # 从第7个字节开始提取
                    print(f"提取的數據: {data_hex}")

                else:
                    print("回應數據長度不符合要求。")
            else:
                print("未接收到數據。")
    
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        client.close()

# 用法示例
#ip_address = '192.168.24.19'  # 替換為你的 IP 地址
#port_number = 10123           # 替換為你的端口號
#test_modbus_request(ip_address, port_number)
from pymodbus.client.tcp import ModbusTcpClient
import binascii
import struct

def calculate_crc(data):
    """计算 CRC-16 校验码"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def create_request(start_address, quantity):
    """创建 Modbus 读取请求"""
    # 请求数据格式：功能码 0x03 + 起始地址 + 寄存器数量 + CRC 校验
    request = struct.pack('>B', 0x03)  # 功能码
    request += struct.pack('>H', start_address)  # 起始寄存器地址
    request += struct.pack('>H', quantity)  # 寄存器数量
    crc = calculate_crc(request)
    request += crc  # 附加 CRC 校验码
    return request

def test_modbus_request(ip, port):
    client = ModbusTcpClient(ip, port)
    
    try:
        if client.connect():
            print("成功連接。")
            
            # 创建 Modbus 读取请求
            start_address = 0x0008
            quantity = 14  # 读取的寄存器数量
            request_bytes = create_request(start_address, quantity)
            print(f"發送的請求: {binascii.hexlify(request_bytes).decode()}")

            # 发送请求
            client.socket.send(request_bytes)
            
            # 接收回應數據
            response_bytes = client.socket.recv(1024)
            if response_bytes:
                hex_data = binascii.hexlify(response_bytes).decode()
                print(f"接收到的十六進位數據: {hex_data}")

                # 解析数据
                if len(response_bytes) >= 7:
                    # 去除 Modbus 地址和功能码，提取数据部分
                    data_hex = hex_data[6*2:]  # 从第7个字节开始提取
                    print(f"提取的數據: {data_hex}")

                else:
                    print("回應數據長度不符合要求。")
            else:
                print("未接收到數據。")
    
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        client.close()

from pymodbus.client.tcp import ModbusTcpClient
import binascii
import struct

def calculate_crc(data):
    """计算 CRC-16 校验码"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def create_request(slave_id, start_address, quantity):
    """创建 Modbus 读取请求"""
    # 构建请求数据
    request = struct.pack('>B', slave_id)  # 仪表地址
    request += struct.pack('>B', 0x03)  # 功能码
    request += struct.pack('>H', start_address)  # 起始寄存器地址
    request += struct.pack('>H', quantity)  # 寄存器数量
    crc = calculate_crc(request)
    request += crc  # 附加 CRC 校验码
    return request

def test_modbus_request(ip, port, slave_id, start_address, quantity):
    client = ModbusTcpClient(ip, port, timeout=10)  # 设置超时时间为 10 秒
    
    try:
        if client.connect():
            print("成功連接。")
            
            # 创建 Modbus 读取请求
            request_bytes = create_request(slave_id, start_address, quantity)
            print(f"發送的請求: {binascii.hexlify(request_bytes).decode()}")

            # 发送请求
            client.socket.send(request_bytes)
            
            # 接收回應數據
            response_bytes = client.socket.recv(1024)
            if response_bytes:
                hex_data = binascii.hexlify(response_bytes).decode()
                print(f"接收到的十六進位數據: {hex_data}")

                # 解析数据
                if len(response_bytes) >= 7:
                    # 去除 Modbus 地址和功能码，提取数据部分
                    data_hex = hex_data[6*2:-4]  # 从第7个字节开始提取，并去掉 CRC
                    print(f"提取的數據: {data_hex}")

                else:
                    print("回應數據長度不符合要求。")
            else:
                print("未接收到數據。")
    
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        client.close()


from pymodbus.client.tcp import ModbusTcpClient
import binascii
import struct

def calculate_crc(data):
    """计算 CRC-16 校验码"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def create_request(slave_id, start_address, quantity):
    """创建 Modbus 读取请求"""
    # 构建请求数据
    request = struct.pack('>B', slave_id)  # 仪表地址
    request += struct.pack('>B', 0x03)  # 功能码
    request += struct.pack('>H', start_address)  # 起始寄存器地址
    request += struct.pack('>H', quantity)  # 寄存器数量
    crc = calculate_crc(request)
    request += crc  # 附加 CRC 校验码
    return request

def test_modbus_request(ip, port, slave_id, start_address, quantity):
    client = ModbusTcpClient(ip, port, timeout=10)  # 设置超时时间为 10 秒
    
    try:
        if client.connect():
            print("成功連接。")
            
            # 创建 Modbus 读取请求
            request_bytes = create_request(slave_id, start_address, quantity)
            print(f"發送的請求: {binascii.hexlify(request_bytes).decode()}")

            # 发送请求
            client.socket.send(request_bytes)
            
            # 接收回應數據
            response_bytes = client.socket.recv(1024)
            if response_bytes:
                hex_data = binascii.hexlify(response_bytes).decode()
                print(f"接收到的十六進位數據: {hex_data}")

                # 解析数据
                if len(response_bytes) >= 7:
                    # 去除 Modbus 地址和功能码，提取数据部分
                    data_hex = hex_data[6*2:-4]  # 从第7个字节开始提取，并去掉 CRC
                    print(f"提取的數據: {data_hex}")

                else:
                    print("回應數據長度不符合要求。")
            else:
                print("未接收到數據。")
    
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        client.close()


def calculate_crc(data):
    """计算 CRC-16 校验码"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def create_request(slave_id, start_address, quantity):
    """创建 Modbus 读取请求"""
    # 构建请求数据
    request = struct.pack('>B', slave_id)  # 仪表地址
    request += struct.pack('>B', 0x03)  # 功能码
    request += struct.pack('>H', start_address)  # 起始寄存器地址
    request += struct.pack('>H', quantity)  # 寄存器数量
    crc = calculate_crc(request)
    request += crc  # 附加 CRC 校验码
    return request

def test_modbus_request(ip, port, slave_id, start_address, quantity):
    client = ModbusTcpClient(ip, port, timeout=10)  # 设置超时时间为 10 秒
    
    try:
        if client.connect():
            print("成功連接。")
            
            # 创建 Modbus 读取请求
            request_bytes = create_request(slave_id, start_address, quantity)
            print(f"發送的請求: {binascii.hexlify(request_bytes).decode()}")

            # 发送请求
            client.socket.send(request_bytes)
            
            # 接收回應數據
            response_bytes = client.socket.recv(1024)
            if response_bytes:
                hex_data = binascii.hexlify(response_bytes).decode()
                print(f"接收到的十六進位數據: {hex_data}")

                # 解析数据
                if len(response_bytes) >= 7:
                    # 去除 Modbus 地址和功能码，提取数据部分
                    data_hex = hex_data[6*2:-4]  # 从第7个字节开始提取，并去掉 CRC
                    print(f"提取的數據: {data_hex}")

                else:
                    print("回應數據長度不符合要求。")
            else:
                print("未接收到數據。")
    
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        client.close()

# 用法示例
ip_address = '192.168.24.19'  # 替換為你的 IP 地址
port_number = 10123           # 替換為你的端口號
slave_id = 1  # 仪表地址
start_address = 0x0008  # 寄存器起始地址
quantity = 14  # 读取的寄存器数量

test_modbus_request(ip_address, port_number, slave_id, start_address, quantity)