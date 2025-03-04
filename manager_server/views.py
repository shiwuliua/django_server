import json
from django.shortcuts import render

from django.http import JsonResponse
from manager_server.cpp_server import send_pdu_to_cpp_server  # 导入处理 C++ 通信的函数
from manager_server.pdu import PDU
from manager_server.pdu import MessageType

# 注册页面视图
def register_page(request):
    if request.method == 'POST':
        try:
            # 解析 JSON 数据
            data = json.loads(request.body)
            print(data)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'status': 'error', 'message': '用户名和密码不能为空'})

            # 构造用户数据
           
            # 调用处理函数与 C++ 服务器交互
            cpp_response = send_pdu_to_cpp_server(MessageType.REGISTER, username,password)

            # 根据 C++ 服务器返回的结果返回响应
            if cpp_response.get('status') == 'success':
                return JsonResponse({'status': 'success', 'message': 'Registration successful'})
            else:
                return JsonResponse({'status': 'error', 'message': cpp_response.get('message', 'Unknown error')})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '无效的 JSON 格式'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'服务器内部错误: {str(e)}'})

    # 对于 GET 请求，返回注册页面
    return render(request, 'register.html')


