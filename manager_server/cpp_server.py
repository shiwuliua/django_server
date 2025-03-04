
import socket
import json

from manager_server.pdu import PDU, MessageType  # 确保你的 PDU 代码存放在 myprotocol.py 中

def send_pdu_to_cpp_server(message_type, username="",password=""):
    """
    该函数接收 Django 视图传入的参数（如账号、密码、邮箱等），
    构造 PDU 并通过 TCP 发送给远程 C++ 服务器。
    
    :param message_type: PDU 消息类型（如 MessageType.LOGIN_REQUEST）
    :param body: PDU 消息体（可包含 JSON 数据）
    :param server_address: 服务器的地址和端口
    :return: 服务器返回的 PDU 响应
    """
  
    server_address=('43.136.84.247', 9090)
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # 1. 连接到远程 C++ 服务器
 
        client_socket.connect(server_address)
       
        
        # 2. 构造 PDU 对象
        
        body_data = {"body": {"username": username, "password": password}}
        body_str=json.dumps(body_data)

        pdu = PDU(message_type, body_str, '1.0')

        # 3. 发送序列化后的 PDU
        message = pdu.serialize()
    
        bytes_data = message.encode('utf-8')
        client_socket.sendall(bytes_data)  # 直接发送字节数据，假设 message 是字节流
        
        # 4. 接收 C++ 服务器的响应
        response = client_socket.recv(4096).decode('utf-8')  # 适当调整缓冲区大小
        response_pdu = PDU.deserialize(response)
           
        return response_pdu

    except socket.error as e:
        print(f"连接失败: {e}")  # 如果连接失败，这里会捕获异常并输出错误信息
        return PDU(MessageType.ERROR, "TCP Communication Error", str(e))
    
    except Exception as e:
        print(f"Error: {e}")
        return PDU(MessageType.ERROR, "TCP Communication Error", str(e))

    finally:
        client_socket.close()  # 无论成功与否，都会关闭 socket
