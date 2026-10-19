from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import threading
import time
import struct
import binascii
import pandas as pd
# 創建全域事件
request_received = threading.Event()
def hex_to_float(hex_str):
    """將十六進位字串轉換為 IEEE 754 單精度浮點數"""
    if len(hex_str) != 8:
        raise ValueError("十六進位字串長度不正確，應為8位")
    return struct.unpack('>f', bytes.fromhex(hex_str))[0]

def parse_switch_status(response):
    # 回應數據以位元組流形式返回，需要提取相關位元組
    if len(response) >= 5:
        # 提取開關量狀態位元組（例如0x02）
        status_byte = response[3]  # 讀取回應中的數據位元組部分
        # 提取開關量狀態，1 = 開關合閉，0 = 開關斷開
        di1 = (status_byte & 0x01) >> 0
        di2 = (status_byte & 0x02) >> 1
        di3 = (status_byte & 0x04) >> 2
        return di1, di2, di3
    else:
        raise ValueError("回應長度無效")

def parse_response_data(hex_data):
    """解析回應數據中的 IEEE 754 單精度浮點數"""
    # 每 8 個十六進位字符（4 個字節）代表一個 IEEE 754 單精度浮點數
    num_floats = len(hex_data) // 8
    float_values = []
    
    for i in range(num_floats):
        float_hex = hex_data[i*8:(i+1)*8]
        try:
            float_value = hex_to_float(float_hex)
            float_values.append(float_value)
        except ValueError as ve:
            print(f"解碼錯誤: {ve}")
    
    return float_values

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

            if len(hex_data) >=14:
                # 提取第七位到第十四位的數據
                data_hex = hex_data[6:14]  # 提取所需數據（16個十六進位字符）
                try:
                    float_value = hex_to_float(data_hex)
                    print(f"解碼得到的浮點數: {float_value}")
                    # 可選：將結果添加到 DataFrame 中
                    # 創建新的 DataFrame 行
                    new_row = pd.DataFrame({"Request": ["N/A"], "Float Value": [float_value]})
                    # 使用 concat 方法將新的行添加到原 DataFrame 中
                    df = pd.concat([df, new_row], ignore_index=True)
                    print(df)
                except ValueError as ve:
                    print(f"解碼錯誤: {ve}")
            else:
                print("接收到的數據長度不足。")
                #else:
                 #   print(f"請求數據未在響應中找到: {request}")
            
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
            # 解析數據
            if len(hex_data) >= 14:
                data_hex = hex_data[6:14]  # 提取所需數據
                try:
                    float_value = hex_to_float(data_hex)
                    print(f"解碼得到的浮點數: {float_value}")
                except ValueError as ve:
                    print(f"解碼錯誤: {ve}")

            else:
                print("接收到的數據長度不符合要求。")
            # 發送請求數據
            #response = client.execute(request_bytes)
            # 發送原始 Modbus 請求
            # 將 request_bytes 從十六進位字串轉換為位元組數據
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
            request_bytes = bytes.fromhex('01 03 00 08 00 0E 45 CC')

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


'''def send_and_receive_tcp_data(ip, port, data_to_send, buffer_size=4096, timeout=20):
    try:
        # 創建一個 TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 設置超時時間
            s.settimeout(timeout)
            # 連接到指定的 IP 和端口
            s.connect((ip, port))
            
            # 將數據轉換為 bytes 格式並發送
            s.sendall(data_to_send)
            
            # 接收數據
            data = s.recv(buffer_size)
            
            # 將數據轉換為 16 進制格式
            hex_data = data.hex()
            
            return hex_data

    except socket.timeout:
        print("Connection or reception timed out.")
        return None
    except socket.error as e:
        print(f"Socket error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# 用法示例
ip_address = '192.168.24.19'  # 替換為你的 IP 地址
port_number = 10123           # 替換為你的端口號

# 要發送的 16 進制數據（01 03 00 08 00 0E 45 CC）
data_to_send = bytes.fromhex('01 03 00 08 00 0E 45 CC')

hexadecimal_data = send_and_receive_tcp_data(ip_address, port_number, data_to_send)
if hexadecimal_data:
    print(f"Received Hex Data: {hexadecimal_data}")
else:
    print("Failed to receive data.")'''

'''import threading
*
def read_tcp_data(ip, port, buffer_size=4096):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, port))
        data = s.recv(buffer_size)
        hex_data = data.hex()
        return hex_data

def threaded_read_tcp_data(ip, port, buffer_size=4096):
    thread = threading.Thread(target=read_tcp_data, args=(ip, port, buffer_size))
    thread.start()
    return thread

# 使用示例
ip_address = '192.168.24.19'
port_number = 10123

thread = threaded_read_tcp_data(ip_address, port_number)
thread.join()  # 等待線程完成'''

