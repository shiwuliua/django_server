from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from manager_server.cpp_server import CppClient  # 导入 CppClient 类
from manager_server.pdu import MessageType


# 序列化 CppClient 对象
def cpp_client_to_json(client):
    return json.dumps(client.__getstate__())

# 反序列化 CppClient 对象
def cpp_client_from_json(data):
    state = json.loads(data)
    client = CppClient(user_id=None)  # 使用适当的构造函数
    client.__setstate__(state)  # 恢复状态
    return client


def register_page(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'status': 'error', 'message': '用户名和密码不能为空'})
            if len(username) < 3:
                return JsonResponse({'status': 'error', 'message': '账户名字长度不能小于三位数'})

            # 构造用户数据
            cpp_client = CppClient(user_id=None)  # 暂时不需要 user_id，先用空值初始化
            cpp_response = cpp_client.send_request(MessageType.REGISTER, username, password)

            if cpp_response['register_statu'] == 'success':
                cpp_client.close()
                return JsonResponse({'status': 'success', 'message': '注册成功'})
            else:
                return JsonResponse({'status': 'error', 'message': cpp_response.get('message', '用户名已经存在')})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '无效的 JSON 格式'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'服务器内部错误: {str(e)}'})

    # 对于 GET 请求，返回注册页面
    return render(request, 'register.html')


def login_page(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'status': 'error', 'message': '用户名和密码不能为空'})
            if len(username) < 3:
                return JsonResponse({'status': 'error', 'message': '账户名字长度不能小于三位数'})

            # 获取 user_id 和 cpp_client 对象
        
            cpp_client = CppClient(user_id=None)

            # 使用 cpp_client 发送登录请求
            login_response_PDU = cpp_client.send_request(
                MessageType.LOGIN_REQUEST, 
                {"username": username, "password": password}
            )

            login_response = json.loads(login_response_PDU.body)

            if login_response_PDU.type == MessageType.LOGIN_SUCCESS:
                user_id = login_response.get('userid')
                if user_id:
                    request.session['user_id'] = user_id
                    request.session['cpp_client'] = cpp_client_to_json(cpp_client)
                    request.session['names']=username
                    
                    # 从登录响应中获取文件系统数据
                    file_system_data = login_response.get('file_list')
                   
                    
                    response_data = {
                        'status': 'success',
                        'message': '登录成功',
                        'fileSystemData': file_system_data
                    }
             
                    return JsonResponse(response_data)
                else:
                    return JsonResponse({'status': 'error', 'message': '用户ID不存在'})
            else:
                return JsonResponse({'status': 'error', 'message': login_response.get('message', '用户名或密码错误')})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '无效的 JSON 格式'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'服务器内部错误: {str(e)}'})


def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            sender = data.get('sender')

            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({'status': 'error', 'message': '用户未登录'})

            cpp_client_json = request.session.get('cpp_client')
            cpp_client = cpp_client_from_json(cpp_client_json)
            if not cpp_client:
                return JsonResponse({'status': 'error', 'message': '用户连接无效'})

            response = cpp_client.send_request(MessageType.SEND_MESSAGE, {"message": message, "sender": sender})

            if response:
                return JsonResponse({'status': 'ok', 'message': '消息接收成功'})
            else:
                return JsonResponse({'status': 'error', 'message': '消息发送失败'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': '仅支持 POST 请求'})

# views.py
def login_success(request):
    return render(request, 'login.html')

def users(request):
    user = request.user  # 获取当前登录的用户
    context = {
        'user': user,
        'storage_used': '2.5GB',  # 示例数据
        'storage_total': '10GB',  # 示例数据
        'storage_percentage': 25,  # 示例数据
    }
    return render(request, 'users.html', context)  # 渲染用户信息页面

@csrf_exempt
def logout_view(request):
    # 清除 session 中存储的 cpp_client 对象并关闭连接
    cpp_client_json = request.session.get('cpp_client')
    if cpp_client_json:
        try:
            cpp_client = cpp_client_from_json(cpp_client_json)
            cpp_client.close()
            request.session.flush()  # 清除所有 session 数据
            return JsonResponse({'success': True, 'msg': '退出成功'})
        except Exception as e:
            print(f"恢复 CppClient 对象时出错: {str(e)}")
            return JsonResponse({'success': False, 'msg': '退出失败'})
    else:
        return JsonResponse({'success': False, 'msg': '没有找到登录连接'})

    
@csrf_exempt
def down_file(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            data["local_file_path"] = "web"  #区分web端 qt端需要回传地址
            data["names"]=request.session.get('names')
            folder_id = data.get("folder_id")
            file_name = data.get("file_name")
            user_id = request.session.get('user_id')

          
            if not user_id:
                return JsonResponse({'status': 'error', 'message': '用户未登录'})
            cpp_client_json = request.session.get('cpp_client')
            cpp_client = cpp_client_from_json(cpp_client_json)
          
            if not cpp_client:
                return JsonResponse({'status': 'error', 'message': '用户连接无效'})

            response_PDU = cpp_client.send_request(MessageType.DOWNLOAD_FILE, data)
            response=json.loads(response_PDU.body)
      
            presigned_url =response.get('url')
            print(presigned_url)

            return JsonResponse({
                "status": "success",
                "download_url": presigned_url
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'服务器内部错误: {str(e)}'})
@csrf_exempt
def share_file(request):
    if request.method == 'POST':
        try:
            print("t1")
            data = json.loads(request.body)
            
            data["local_file_path"] = "web"  #区分web端 qt端需要回传地址
            data["names"]=request.session.get('names')
            folder_id = data.get("folder_id")
            file_name = data.get("file_name")
            user_id = request.session.get('user_id')

        
            if not user_id:
                return JsonResponse({'status': 'error', 'message': '用户未登录'})
            cpp_client_json = request.session.get('cpp_client')
            cpp_client = cpp_client_from_json(cpp_client_json)
          
            if not cpp_client:
                return JsonResponse({'status': 'error', 'message': '用户连接无效'})
            

            response_PDU = cpp_client.send_request(MessageType.SHARE_FILE, data)
            response=json.loads(response_PDU.body)
            presigned_url =response.get('url')
            print(presigned_url)
            return JsonResponse({
                "status": "success",
                "share_url": presigned_url
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'服务器内部错误: {str(e)}'})