from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import threading
import time
import struct
import binascii
import pandas as pd
# 創建全域事件
request_received = threading.Event()
def send_request(client, requests):
    """定時發送 Modbus 請求"""
    #while True:
    try:
        for request in requests:
            #try:
                # 要發送的請求數據（例如：01 03 00 08 00 0E 45 CC）
                request_bytes = bytes.fromhex(request)
                client.socket.send(request_bytes)
                print("發送請求成功")
                request_received.set()  # 通知讀取線程已發送請求
                time.sleep(1)  # 定時發送間隔（例如每5秒）
    except Exception as e:
                print(f"發送請求時發生錯誤: {e}")

def read_response(client):
    """讀取 Modbus 回應"""
    global request_received
    requests = []
    try:
        df = pd.DataFrame(columns=["Request", "Float Value"])
        while True:
            response_bytes = client.socket.recv(4096)  # 接收數據
            if not response_bytes:
                print("未接收到數據，重新連接...")
                client.close()
                # 嘗試重新連接
                client.connect()
                continue
            
            # 將響應數據轉換為十六進位字串
            hex_data = binascii.hexlify(response_bytes).decode()
            print(f"接收到的十六進位數據: {hex_data}")
            
            request_received.clear()  # 重置通知狀態
            
    except Exception as e:
        print(f"讀取回應時發生錯誤: {e}")

def send_request_and_read(ip, port):
    # 創建 Modbus TCP 客戶端
    client = ModbusTcpClient(ip, port, timeout=10)  # 增加超時時間為10秒
    
    try:
        # 連接到 Modbus 伺服器
        if client.connect():
            print("成功連接。")
            # 發送 Modbus 請求
            # 讀取保持寄存器（示範請求，請根據實際情況修改功能碼和寄存器範圍）
            # response = client.read_holding_registers(0x0008, 7, unit=1)
            request_bytes = bytes.fromhex('01 03 00 08 00 0E 45 CC')  # 你要發送的請求
            client.socket.send(request_bytes)
            response_bytes = client.socket.recv(1024)  # 接收數據
            # 將響應數據轉換為十六進位字串
            hex_data = binascii.hexlify(response_bytes).decode()
            print(f"接收到的十六進位數據: {hex_data}")
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

# 要發送的請求數據（01 03 00 08 00 0E 45 CC）
#request_bytes = '01 03 00 08 00 0E 45 CC'

# 嘗試發送請求並讀取數據
#send_request_and_read(ip_address, port_number)
def main(ip, port, requests):
    # 創建 Modbus TCP 客戶端
    client = ModbusTcpClient(ip, port, timeout=120)  # 增加超時時間為120秒

    try:
        if client.connect():
            print("成功連接。")

            # 要發送的請求數據（例如：01 03 00 08 00 0E 45 CC）
            request_bytes = bytes.fromhex(requests)

            # 創建線程來發送請求和讀取回應
            send_thread = threading.Thread(target=send_request, args=(client, requests))
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
ip_address = '192.168.24.19'  # 替換為你的 Modbus TCP 伺服器 IP 地址
port_number = 10123           # 替換為你的端口號
# 多個請求數據
requests = [
    '01 03 00 08 00 02 45 C9',  # 供温瞬时值
    '01 03 00 0A 00 02 E4 09',  # 回温瞬时值
    '01 03 00 0E 00 02 A5 C8',  # 流量瞬时值
    '01 03 00 14 00 02 84 0F' # 流量总累积量
    '01 03 00 16 00 02 25 CF' # 熱能瞬時值
    '01 03 00 18 00 02 44 0C' # 熱能累積值
    # 可以添加更多請求
]
# 嘗試發送請求並讀取數據
main(ip_address, port_number, requests)


