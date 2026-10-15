from django.urls import path
from . import views

app_name='users'

urlpatterns = [
    path('send-otp', views.send_otp_phone, name='send-otp-phone'),
    path('verify-otp', views.verify_otp, name='verify-otp'),
    
]