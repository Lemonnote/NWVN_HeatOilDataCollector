from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import threading
import time
import binascii
import pandas as pd
from queue import Queue
import struct
import pyodbc
from sqlalchemy import create_engine
from datetime import datetime

# 創建一個標誌來指示是否已接收到數據
data_received = threading.Event()

def parse_modbus_response(response_str):
    """解析 Modbus 回應"""
    print("正在解析 Modbus 回應...")
    # Convert the response string to a byte array
    response_bytes = bytes.fromhex(response_str)
    
    # Extract the bytes from the fourth byte onwards
    data_bytes = response_bytes[3:]
    
    # Function to reorder byte array
    def reorder_byte_array(byte_array):
        # Define new order
        new_order = [0, 1, 2, 3]
        # Reorder byte array
        reordered_array = [byte_array[i] for i in new_order]
        return reordered_array
    
    # Define the function to convert byte string to float
    def bytes_to_float(byte_str):
        bytes_seq = bytes.fromhex(byte_str.replace(' ', ''))
        return struct.unpack('>f', bytes_seq)[0]
    
    # Prepare the byte array in the correct format
    byte_array = [
        ' '.join(format(data_bytes[i*4+j], '02X') for j in range(4))
        for i in range(len(data_bytes) // 4)
    ]
    
    # Reorder each byte string in the byte array
    reordered_byte_array = [' '.join(format(b, '02X') for b in reorder_byte_array([int(x, 16) for x in byte_str.split()])) for byte_str in byte_array]
    
    print("重新排序後的字節數組:", reordered_byte_array)
    # Parse all values
    parsed_values = [bytes_to_float(b) for b in reordered_byte_array]
    
    print("解析後的值:", parsed_values)
    return parsed_values

def send_request(client, requests, response_queue):
    """定時發送 Modbus 請求"""
    try:
        for request in requests:
            request_bytes = bytes.fromhex(request)
            client.socket.send(request_bytes)
            print(f"發送請求成功: {request}")
            time.sleep(1)  # 定時發送間隔（例如每1秒）
    except Exception as e:
        print(f"發送請求時發生錯誤: {e}")
    finally:
        response_queue.put(None)  # 通知讀取線程結束

def read_response(client, response_queue):
    """讀取 Modbus 回應"""
    try:
        while True:
            response_bytes = client.socket.recv(4096)  # 接收數據
            if not response_bytes:
                print("未接收到數據，結束")
                client.close()
                break
            # 將響應數據轉換為十六進位字串
            hex_data = binascii.hexlify(response_bytes).decode()
            print(f"接收到的十六進位數據: {hex_data}")
            
            # 解析數據
            parsed_values = parse_modbus_response(hex_data)
            print(f"解析後的值: {parsed_values}")
            
            # 將數據放入隊列
            response_queue.put(parsed_values)
            
            # 設置數據接收標誌
            data_received.set()
            break  # 只接收第一筆數據後跳出循環
    except Exception as e:
        print(f"讀取回應時發生錯誤: {e}")
    finally:
        response_queue.put(None)  # 通知主線程結束

def upload_to_sql_server(data):
    """將數據上傳到 SQL Server"""
    print("正在上傳數據到 SQL Server...")
    server = '192.168.24.170'  # 伺服器名稱
    database = 'BatchDyeingCentral'  # 數據庫名稱
    username = 'spc'  # 使用者名稱
    password = '84160206'  # 密碼
    driver = 'ODBC Driver 17 for SQL Server'  # ODBC 驅動程式

    connection_string = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}'
    engine = create_engine(connection_string)

    try:
        data.to_sql('Consumption_HeatOil', con=engine, if_exists='append', index=False)
        print("數據成功上傳到 SQL Server。")
    except Exception as e:
        print(f"數據上傳時發生錯誤: {e}")

def main(ip, port, requests):
    print("初始化 Modbus TCP 客戶端...")
    # 創建 Modbus TCP 客戶端
    client = ModbusTcpClient(host=ip, port=port, timeout=10)  # 確保參數正確

    try:
        if client.connect():
            print("成功連接。")

            # 去除請求中的空格
            cleaned_requests = [request.replace(' ', '') for request in requests]

            # 創建隊列來在線程之間傳遞數據
            response_queue = Queue()

            # 創建線程來發送請求和讀取回應
            send_thread = threading.Thread(target=send_request, args=(client, cleaned_requests, response_queue))
            read_thread = threading.Thread(target=read_response, args=(client, response_queue))

            # 啟動線程
            send_thread.start()
            read_thread.start()

            # 等待數據接收標誌
            data_received.wait()

            # 處理接收到的數據
            all_data = []
            while not response_queue.empty():
                parsed_values = response_queue.get()
                if parsed_values is None:
                    break
                # 構建數據行
                if len(parsed_values) >= 15:
                    data_row = {
                        "Machine": 'F01',
                        "OilSupplyTemperature": parsed_values[0],
                        "OilReturnTemperature": parsed_values[1],
                        "RealTimeFlow": parsed_values[3],
                        "TotalFlowVolume": parsed_values[6],
                        "RealTimeHeatValue": parsed_values[13],
                        "TotalHeatValue": parsed_values[14],
                        "CreateTime": datetime.now()
                    }
                    all_data.append(data_row)
            
            # 創建數據框並上傳到 SQL Server
            if all_data:
                df = pd.DataFrame(all_data)
                upload_to_sql_server(df)
        else:
            print("連接失敗。")

    except ModbusException as e:
        print(f"Modbus 異常: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        # 斷開連接
        client.close()
        print("程式結束。")

# 用法示例
ip_address = '192.168.24.19'  # 替換為你的 Modbus TCP 伺服器 IP 地址
port_number = 10123           # 替換為你的端口號
requests = [
    '01 03 00 07 00 3C F4 1A',
    '01 03 00 07 00 3C F4 1A',
    '01 03 00 07 00 3C F4 1A'
    # 可以添加更多請求
]

print("開始運行程式...")
# 嘗試發送請求並讀取數據
main(ip_address, port_number, requests)
print("程式運行結束。")