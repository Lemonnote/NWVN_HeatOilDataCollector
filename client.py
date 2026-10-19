import socket

# 定义服务器IP地址和端口
IP_ADDRESS = '192.168.24.19'
PORT = 10123

# 要发送的字节数据
send_data = bytes([0x01, 0x03, 0x00, 0x08, 0x00, 0x0E, 0x45, 0xCC])

def main():
    # 创建TCP/IP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # 连接到服务器
        sock.connect((IP_ADDRESS, PORT))
        print("Connected to the server...")

        # 发送数据
        sock.sendall(send_data)
        print(f"Sent {len(send_data)} bytes to server")

        # 接收数据
        recv_data = sock.recv(1024)
        print(f"Received {len(recv_data)} bytes from server")
        
        # 打印接收到的字节数据
        print("Received data:", ' '.join(f'{byte:02x}' for byte in recv_data))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 关闭连接
        sock.close()

if __name__ == "__main__":
    main()
