import json
from enum import Enum


class MessageType(Enum):
    LOGIN_REQUEST = 0x01
    LOGIN_RESPONSE = 0x02
    LOGIN_SUCCESS = 0x03
    GROUPS_MESSAGES = 0x04
    FRIENDS_MESSAGES = 0x05
    GET_FRIENDS = 0x06
    GET_FILELIST = 0x07
    RESPONSE_GET_FILELIST = 0x08
    DOWNLOAD_FILE = 0x10
    ERROR = 0x11
    LOGIN_FAIL = 0x09
    ADD_NEW_FOLDER = 0x13
    ADD_NEW_FILE = 0x14
    UPLOAD_FILE = 0x15
    DELETE_FILE = 0x16
    RENAME_FILE = 0x17
    DELETE_FOLDER = 0x18
    PASTE_FILE = 0x19
    REGISTER = 0x20
    SHARE_FILE=0x21


class PDU:
    def __init__(self, type: MessageType, body: str = "", header: str = ""):
        self.type = type
        self.header = header
        self.body = body
        self.length = 4 + 4 + len(header) + len(body)  # length = sizeof(length) + sizeof(type) + len(header) + len(body)

    def serialize(self) -> str:
        """序列化 PDU 对象为 JSON 字符串"""
        data = {
            "length": self.length,
            "type": self.type.value,
            "header": self.header,
            "body": self.body
        }
        return json.dumps(data)

    @staticmethod
    def deserialize(data: str):
        """反序列化 JSON 字符串为 PDU 对象"""
        try:
            j = json.loads(data)

            if "type" not in j or not isinstance(j["type"], int):
                return PDU(MessageType.ERROR, "Invalid 'type'", "Invalid JSON")

            if "header" not in j or not isinstance(j["header"], str):
                return PDU(MessageType.ERROR, "Invalid 'header'", "Invalid JSON")

            body = j.get("body", "")

            # 计算 length
            length = 4 + 4 + len(j["header"]) + len(body)

            return PDU(MessageType(j["type"]), body, j["header"])

        except json.JSONDecodeError:
            return PDU(MessageType.ERROR, "JSON parse error", "Invalid JSON")
        except Exception:
            return PDU(MessageType.ERROR, "Deserialization error", "Invalid JSON")
