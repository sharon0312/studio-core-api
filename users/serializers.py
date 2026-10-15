from rest_framework import serializers



class PhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    phone_code = serializers.CharField(max_length=5)

    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        return value
    
    
class OTPSerializer(PhoneSerializer):
    otp = serializers.CharField(max_length=6)
    phone_code=serializers.CharField()
    phone_number=serializers.CharField()

    def validate_otp(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP must be exactly 6 digits.")
        return value
    
    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        return value