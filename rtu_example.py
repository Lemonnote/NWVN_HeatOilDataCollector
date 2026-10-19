"""
Modbus RTU 獨立範例
可直接執行測試 RTU 通訊，或作為參考改寫為其他用途。

預設設定 (對應流量計錶頭):
  - Slave ID: 1
  - Function Code: 03 (Read Holding Registers)
  - Start Address: 7  (對應 40008)
  - Register Count: 14 (讀取 40008~40021)

使用方式:
    python rtu_example.py

或修改 config.json 中的 modbus_rtu 區塊後執行 HeatOilFlowmeter.py
"""

from pymodbus.client.serial import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import struct
import time

# 自行調整或從 config.json 載入
RTU_CONFIG = {
    "port": "COM1",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "slave_id": 1,
    "start_address": 7,
    "register_count": 14
}


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


def parse_registers_to_floats(registers):
    """將 register list (big-endian 16-bit) 轉換為 float list (ABCD -> DCBA)"""
    data_bytes = b''.join(struct.pack('>H', reg) for reg in registers)
    
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

    return [bytes_to_float(b) for b in reordered_byte_array]


def main():
    cfg = RTU_CONFIG
    print(f"連線: {cfg['port']} @ {cfg['baudrate']},8,{cfg['parity']},{cfg['stopbits']}")
    
    client = ModbusSerialClient(
        port=cfg['port'],
        baudrate=cfg['baudrate'],
        bytesize=cfg['bytesize'],
        parity=cfg['parity'],
        stopbits=cfg['stopbits'],
        timeout=3
    )

    try:
        if not client.connect():
            print("連接失敗，請確認串口已連接。")
            return

        print(f"成功連接，讀取暫存器 {cfg['start_address']}~{cfg['start_address'] + cfg['register_count'] - 1}")
        
        result = client.read_holding_registers(
            address=cfg['start_address'],
            count=cfg['register_count'],
            slave=cfg['slave_id']
        )

        if result.isError():
            print(f"Modbus 錯誤: {result}")
            return

        print(f"收到 {len(result.registers)} 個暫存器值: {result.registers}")
        
        floats = parse_registers_to_floats(result.registers)
        print("\n=== 解析結果 ===")
        
        # 對應圖片中的暫存器位址
        float_labels = [
            ("40008 (油溫供應)", 0),
            ("40009", 1),
            ("40010 (油溫回傳)", 2),
            ("40011", 3),
            ("40012 (瞬時流量)", 4),
            ("40013", 5),
            ("40014", 6),
            ("40015", 7),
            ("40016 (累積流量)", 8),
            ("40017", 9),
            ("40018 (熱量瞬時)", 10),
            ("40019", 11),
            ("40020 (熱量累積)", 12),
            ("40021", 13),
        ]
        
        for label, idx in float_labels:
            if idx < len(floats):
                print(f"  {label}: {floats[idx]:.4f}")

    except ModbusException as e:
        print(f"Modbus 異常: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        client.close()
        print("\n連線已關閉。")


if __name__ == '__main__':
    main()
