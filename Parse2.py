import struct

def parse_modbus_response(response_str):
    # Convert the response string to a byte array
    response_bytes = bytes.fromhex(response_str)
    
    # Extract the bytes from the fourth byte onwards
    data_bytes = response_bytes[3:]
    
    # Function to reorder byte array
    def reorder_byte_array(byte_array):
        # Define new order
        new_order = [2, 3, 0, 1]
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
    
    print(reordered_byte_array)
    # Parse all values
    parsed_values = [bytes_to_float(b) for b in reordered_byte_array]
    
    return parsed_values

# Given Modbus RTU response string
response_str = "01 03 3C 00 37 43 86 E6 66 43 70 CC CD 43 1B 0A 7A 43 1B 0A 7A 44 59 80 00 41 89 99 9A 47 DE E3 D4 00 00 00 00 00 00 00 00 00 00 00 00 C7 DE E3 D4 C7 DE E3 D4 42 A4 14 78 46 2C E8 0D 4A 61 B0 C3"

# Parsing the response
parsed_values = parse_modbus_response(response_str)
print(parsed_values)
