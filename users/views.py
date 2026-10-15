from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users import serializers
from users import models as user_models
import random
from django.contrib.auth.models import User
from django.db.models import Q,Sum
from studio_core import helper
from studio_core import settings

# Create your views here.


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp_phone(request):
    serializer = serializers.PhoneSerializer(data=request.data)
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST,helper.get_serializer_first_error(serializer))
    data = serializer.validated_data
    generate_otp = 000000
    try:
        phone_number = data['phone_code'] + data['phone_number']
        user_otp = user_models.UserOTP.objects.filter(phone_number=phone_number).first()
        if user_otp:
            user_otp.delete()
        generate_otp = str(random.randint(100000, 999999))
        create_otp = user_models.UserOTP.objects.create(phone_number=phone_number,otp=generate_otp)
        # send_otp_sms = helper.send_otp_sms(phone=data['phone_number'],otp=generate_otp)
        # numbers = [phone_number]
        # send_otp = helper.send_whatsapp_bulk_helper(numbers,generate_otp)
    except Exception as e:
        return helper.failure(status.HTTP_400_BAD_REQUEST,str(e))
    return helper.success(status.HTTP_200_OK,"Otp sent successfully on phone",data={"otp":generate_otp})



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = serializers.OTPSerializer(data=request.data)
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST,helper.get_serializer_first_error(serializer))
    data = serializer.validated_data
    email = data.get('email')
    phone_code = data.get('phone_code')
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    user_role = None
    if not email and not (phone_code and phone_number):
        return helper.failure(status.HTTP_400_BAD_REQUEST,"At least email or phone number should be given",error=[])
    phone = f"{phone_code}{phone_number}"
    user_otp = user_models.UserOTP.objects.filter(phone_number=phone).first()
    if not user_otp:
        return helper.failure(status.HTTP_400_BAD_REQUEST,"Please request an OTP first",error=[])
    if str(otp) != settings.DEFAULT_OTP and str(user_otp.otp) != str(otp):
        return helper.failure(status.HTTP_400_BAD_REQUEST,"Invalid OTP",error=[])
    user = User.objects.filter(username=phone).first()
    if not user:
        user = user_models.User.objects.create_user(username=phone,password='')
        user_details_data = {
            "user": user,
            "phone_code": phone_code if phone_number else None,
            "phone_number": phone_number if phone_number else None,
        }
        user_created = user_models.UserDetail.objects.create(**user_details_data)
    refresh = RefreshToken.for_user(user)
    user_detail = user.details.first()
    user_role = user_detail.role if user_detail else None
    data = {
        'refresh_token': str(refresh),
        'access_token': str(refresh.access_token),
        'user_role': user_role
    }
    user_otp.delete()
    return helper.success(status.HTTP_200_OK, "Otp verified successfully",data)