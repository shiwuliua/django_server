from django.urls import path
from manager_server import views

urlpatterns = [
    
    path('register/', views.register_page, name='register_page'),
    path('login/', views.login_page, name='login_page'),
    path('login_success/', views.login_success, name='login_success'),
    path('users/', views.users, name='users'),
    path('down_file/',views.down_file,name='down_file'),
    path('share_file/',views.share_file,name='share_file'),
]
