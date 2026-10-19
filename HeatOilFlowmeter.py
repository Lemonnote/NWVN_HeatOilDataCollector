from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.client.serial import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import threading
import time
import binascii
import pandas as pd
from queue import Queue
import struct
from sqlalchemy import create_engine
from datetime import datetime

from config import (
    get_config,
    get_modbus_mode,
    get_machine_name,
    get_tcp_settings,
    get_rtu_settings,
    get_modbus_requests,
    get_data_mapping,
    get_sql_settings,
    build_sql_connection_string,
)

# 創建一個標誌來指示是否已接收到數據
data_received = threading.Event()

def parse_floats_from_bytes(data_bytes):
    """將原始 byte 資料解析為 float 列表 (每 4 bytes 一個 float)"""
    def reorder_byte_array(byte_array):
        new_order = [0, 1, 2, 3]
        return [byte_array[i] for i in new_order]

    def bytes_to_float(byte_str):
        bytes_seq = bytes.fromhex(byte_str.replace(' ', ''))
        return struct.unpack('>f', bytes_seq)[0]

    byte_array = [
        ' '.join(format(data_bytes[i*4+j], '02X') for j in range(4))
        for i in range(len(data_bytes) // 4)
    ]

    reordered_byte_array = [
        ' '.join(format(b, '02X') for b in reorder_byte_array([int(x, 16) for x in byte_str.split()]))
        for byte_str in byte_array
    ]

    parsed_values = [bytes_to_float(b) for b in reordered_byte_array]
    return parsed_values


def parse_modbus_response(response_str):
    """解析 Modbus 回應 (TCP 模式: 原始十六進位字串)"""
    print("正在解析 Modbus 回應...")
    response_bytes = bytes.fromhex(response_str)
    data_bytes = response_bytes[3:]  # 跳過前 3 bytes (slave + func + byte_count)
    parsed_values = parse_floats_from_bytes(data_bytes)
    print("解析後的值:", parsed_values)
    return parsed_values


def calculate_crc(data):
    """計算 Modbus RTU CRC-16 校驗碼 (0xA001 多項式)"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')


def build_rtu_request(slave_id, func_code, start_address, register_count):
    """組建 Modbus RTU 請求封包 (含 CRC)"""
    request = bytes([
        slave_id,
        func_code,
        (start_address >> 8) & 0xFF,
        start_address & 0xFF,
        (register_count >> 8) & 0xFF,
        register_count & 0xFF
    ])
    crc = calculate_crc(request)
    return request + crc


def parse_registers_to_floats(registers):
    """將 pymodbus register list (int) 轉換為 float list"""
    # 每個 register = 2 bytes big-endian
    data_bytes = b''.join(struct.pack('>H', reg) for reg in registers)
    return parse_floats_from_bytes(data_bytes)

def send_and_receive_tcp(client, requests, response_queue):
    """使用原始 socket 發送請求並讀取 TCP 回應"""
    try:
        for request in requests:
            request_bytes = bytes.fromhex(request)
            client.socket.send(request_bytes)
            print(f"發送請求成功: {request}")
            time.sleep(1)
    except Exception as e:
        print(f"發送請求時發生錯誤: {e}")
    finally:
        response_queue.put(None)

    try:
        while True:
            response_bytes = client.socket.recv(4096)
            if not response_bytes:
                print("未接收到數據，結束")
                client.close()
                break
            hex_data = binascii.hexlify(response_bytes).decode()
            print(f"接收到的十六進位數據: {hex_data}")

            parsed_values = parse_modbus_response(hex_data)
            print(f"解析後的值: {parsed_values}")

            response_queue.put(parsed_values)
            data_received.set()
            break
    except Exception as e:
        print(f"讀取回應時發生錯誤: {e}")
    finally:
        response_queue.put(None)


def send_and_receive_rtu(client, slave_id, start_address, register_count, response_queue):
    """發送 Modbus RTU 請求並讀取回應 (使用 pymodbus API)"""
    try:
        print(f"發送 RTU 請求: slave={slave_id}, addr={start_address}, count={register_count}")
        result = client.read_holding_registers(
            address=start_address,
            count=register_count,
            slave=slave_id
        )
        if result.isError():
            print(f"RTU 回應錯誤: {result}")
            response_queue.put(None)
            return
        parsed_values = parse_registers_to_floats(result.registers)
        print(f"解析後的值: {parsed_values}")
        response_queue.put(parsed_values)
        data_received.set()
    except Exception as e:
        print(f"RTU 通訊時發生錯誤: {e}")
    finally:
        response_queue.put(None)

def upload_to_sql_server(data, sql_settings=None):
    """將數據上傳到 SQL Server"""
    print("正在上傳數據到 SQL Server...")
    if sql_settings is None:
        sql_settings = get_sql_settings()

    connection_string = build_sql_connection_string(sql_settings)
    engine = create_engine(connection_string)

    try:
        data.to_sql('Consumption_HeatOil', con=engine, if_exists='append', index=False)
        print("數據成功上傳到 SQL Server。")
    except Exception as e:
        print(f"數據上傳時發生錯誤: {e}")

def create_modbus_client(mode=None):
    """根據設定建立 Modbus 客戶端 (TCP 或 RTU)"""
    if mode is None:
        mode = get_modbus_mode()

    if mode == 'rtu':
        rtu = get_rtu_settings()
        print(f"初始化 Modbus RTU 客戶端 ({rtu.get('port', 'COM1')} @ {rtu.get('baudrate', 9600)})...")
        client = ModbusSerialClient(
            port=rtu.get('port', 'COM1'),
            baudrate=rtu.get('baudrate', 9600),
            bytesize=rtu.get('bytesize', 8),
            parity=rtu.get('parity', 'N'),
            stopbits=rtu.get('stopbits', 1),
            timeout=10
        )
    else:
        tcp = get_tcp_settings()
        print(f"初始化 Modbus TCP 客戶端 ({tcp.get('host', '127.0.0.1')}:{tcp.get('port', 502)})...")
        client = ModbusTcpClient(
            host=tcp.get('host', '127.0.0.1'),
            port=tcp.get('port', 502),
            timeout=10
        )
    return client, mode


def build_data_row(parsed_values, machine_name):
    """根據設定檔 data_mapping 從解析後的 float list 組建資料字典"""
    mapping = get_data_mapping()

    idx_supply = mapping.get('oil_supply_temp_index', 0)
    idx_return = mapping.get('oil_return_temp_index', 1)
    idx_flow = mapping.get('realtime_flow_index', 3)
    idx_total = mapping.get('total_flow_index', 6)
    idx_heat = mapping.get('realtime_heat_index', 13)
    idx_total_heat = mapping.get('total_heat_index', 14)

    def safe_get(values, index):
        if index is None or index < 0 or index >= len(values):
            return None
        return values[index]

    return {
        "Machine": machine_name,
        "OilSupplyTemperature": safe_get(parsed_values, idx_supply),
        "OilReturnTemperature": safe_get(parsed_values, idx_return),
        "RealTimeFlow": safe_get(parsed_values, idx_flow),
        "TotalFlowVolume": safe_get(parsed_values, idx_total),
        "RealTimeHeatValue": safe_get(parsed_values, idx_heat),
        "TotalHeatValue": safe_get(parsed_values, idx_total_heat),
        "CreateTime": datetime.now()
    }


def main(requests=None):
    cfg = get_config()
    machine_name = get_machine_name()
    mode = get_modbus_mode()

    client, mode = create_modbus_client(mode)

    try:
        if not client.connect():
            print("連接失敗。")
            return

        print(f"成功連接 (模式: {mode.upper()})。")
        response_queue = Queue()

        if mode == 'rtu':
            rtu = get_rtu_settings()
            slave_id = rtu.get('slave_id', 1)
            start_address = rtu.get('start_address', 7)
            register_count = rtu.get('register_count', 60)
            send_and_receive_rtu(client, slave_id, start_address, register_count, response_queue)
        else:
            if requests is None:
                requests = get_modbus_requests()
            cleaned_requests = [request.replace(' ', '') for request in requests]
            tcp_thread = threading.Thread(
                target=send_and_receive_tcp,
                args=(client, cleaned_requests, response_queue)
            )
            tcp_thread.start()
            data_received.wait(timeout=30)
            tcp_thread.join(timeout=5)

        # 處理接收到的數據
        all_data = []
        while not response_queue.empty():
            parsed_values = response_queue.get()
            if parsed_values is None:
                break
            data_row = build_data_row(parsed_values, machine_name)
            all_data.append(data_row)
        
        if all_data:
            df = pd.DataFrame(all_data)
            upload_to_sql_server(df)
        else:
            print("未收到任何有效數據。")

    except ModbusException as e:
        print(f"Modbus 異常: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        client.close()
        print("程式結束。")


if __name__ == '__main__':
    print("開始運行程式...")
    main()
    print("程式運行結束。")