import struct
import binascii

def hex_to_float(hex_str):
    """將十六進位字串轉換為 IEEE 754 單精度浮點數"""
    # 確保輸入的十六進位字串長度為8位（4個字節）
    if len(hex_str) != 8:
        raise ValueError("十六進位字串長度不正確，應為8位")
    return struct.unpack('>f', bytes.fromhex(hex_str))[0]

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

# 回應數據（以十六進位字串表示）
response_hex = '01031c4383436d199a431ba8f5431ba8f444598000418a666647d90112000094a4'

# 提取第七位到第十四位的數據
data_hex = response_hex[6:14]  # 注意這里是第七位到第十四位，索引從0開始計算

# 將十六進位數據轉換為 IEEE 754 單精度浮點數
try:
    float_values = parse_response_data(data_hex)
    for idx, value in enumerate(float_values):
        print(f"浮點數 {idx + 1}: {value}")
except Exception as e:
    print(f"發生錯誤: {e}")
