import binascii

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
    return crc.to_bytes(2, byteorder='little')

# 示例数据
data = bytes.fromhex('01 03 00 14 00 0E')
crc = calculate_crc(data)
print(f"计算的 CRC 校验码: {binascii.hexlify(crc).decode().upper()}")
