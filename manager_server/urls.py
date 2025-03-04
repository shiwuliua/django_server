from django.urls import path
from manager_server import views

urlpatterns = [
    
    path('register/', views.register_page, name='register_page'),
]
