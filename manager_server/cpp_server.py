import socket
import json
from manager_server.pdu import PDU, MessageType

class CppClient:
    def __init__(self, user_id, server_host='43.136.84.247', server_port=9090):
        print("初始化成功")
        self.user_id = user_id
        self.server_address = (server_host, server_port)
        self.socket = None  # socket会在需要时初始化

    def get_connection(self):
        """ 获取连接，如果不存在则创建新的连接 """
        if not self.socket:  # 如果连接还没有建立
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.socket.connect(self.server_address)
                print(f"[CppClient] 用户 {self.user_id} 成功连接到服务器 {self.server_address}")
            except socket.error as e:
                print(f"[CppClient] 用户 {self.user_id} 连接失败: {e}")
                self.socket = None
        return self.socket

    def receive_until_star(self, conn, chunk_size=8192):
        """接收直到遇到 '*' 字符"""
        data = b''  # 使用字节对象来存储接收到的数据
        while True:
            chunk = conn.recv(chunk_size)
            if not chunk:
                break  # 如果没有数据返回，停止接收
            data += chunk
            # 检查是否包含 '*' 字符，表示数据接收完成
            if b'*' in data:
                break  # 找到 '*' 后跳出循环

        # 返回去掉最后一个 '*' 的解码数据
        return data.decode('utf-8').rstrip('*')

    def send_request(self, message_type, body_dict: dict):
        try:
            conn = self.get_connection()  # 获取连接
            if not conn:
                raise Exception("无法建立与服务器的连接")

            # 构造消息体
            body_str = json.dumps({"body": body_dict})
            pdu = PDU(message_type, body_str, '1.0')
            message = pdu.serialize()

            # 发送消息
            conn.sendall(message.encode('utf-8'))
            # 接收响应
            response = self.receive_until_star(conn)
            # 解析响应
            response_data = PDU.deserialize(response)
            
            return response_data

        except socket.error as e:
            print(f"[ERROR] 网络错误: {str(e)}")
            raise Exception(f"网络连接错误: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 解析错误: {str(e)}")
            raise Exception(f"JSON 解析错误: {str(e)}")
        except Exception as e:
            print(f"[ERROR] 未知错误: {str(e)}")
            raise Exception(f"发生错误: {str(e)}")

    def close(self):
        """ 关闭连接 """
        if self.socket:
            self.socket.close()
            self.socket = None
            print(f"[CppClient] 用户 {self.user_id} 连接已关闭")

    # 序列化：将对象的状态转换为可存储的字典
    def __getstate__(self):
        state = self.__dict__.copy()  # 获取所有实例变量
        if 'socket' in state:
            state['socket'] = None  # 忽略socket对象
        return state

    # 反序列化：根据字典恢复对象的状态
    def __setstate__(self, state):
        self.__dict__.update(state)  # 恢复状态
        self.socket = None  # 反序列化后socket置为None，需要通过get_connection恢复

