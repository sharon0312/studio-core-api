
from rest_framework import serializers
from .models import StudioClass,CreditPack
from studios.models import Studio
from users.models import UserDetail
from studio_core.helper import validate_timezone
from django.utils import timezone


class StudioClassInputSerializer(serializers.Serializer):
    studio_uuid = serializers.UUIDField()
    name = serializers.CharField(max_length=150)
    start_time = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=1)
    spots = serializers.IntegerField(min_value=1)
    credit_cost = serializers.IntegerField(min_value=1)

    def validate_studio_uuid(self, value):
        if not Studio.objects.filter(uuid=value).exists():
            raise serializers.ValidationError("Studio not found.")
        return value


class StudioClassSerializer(serializers.ModelSerializer):
    studio_uuid = serializers.UUIDField(source="studio.uuid", read_only=True)
    # available_spots = serializers.SerializerMethodField()

    class Meta:
        model = StudioClass
        fields = ["uuid", "studio_uuid", "name", "start_time", "duration_minutes", "spots", "credit_cost", "created_at"]

    # def get_available_spots(self, obj):
    #     from bookings.models import Booking
    #     booked = Booking.objects.filter(studio_class=obj, status="CONFIRMED").count()
    #     return max(obj.spots - booked, 0)
    
    
class StudioClassListSerializer(serializers.ModelSerializer):
    # studio_uuid = serializers.UUIDField(source="studio.uuid", read_only=True)
    studio_name = serializers.CharField(source="studio.name", read_only=True)

    class Meta:
        model = StudioClass
        fields = ["uuid", "studio_name", "name", "start_time", "duration_minutes", "spots", "credit_cost", "created_at"]
        
        
class MembersListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.first_name")
    current_credits = serializers.SerializerMethodField()

    class Meta:
        model = UserDetail
        fields = ["uuid", "name","phone_code","phone_number","current_credits","created_at"]
        
    
    def get_current_credits(self, obj):
        return sum(
            CreditPack.objects.filter(member=obj.user,expires_at__gt=timezone.now(),).values_list("remaining_credits", flat=True))



# class CreditGrantInputSerializer(serializers.Serializer):
#     member_uuid = serializers.UUIDField()
#     credits = serializers.IntegerField(min_value=1)
#     expires_at = serializers.DateTimeField()

#     def validate_member_uuid(self, value):
#         if not UserDetail.objects.filter(
#             uuid=value,
#             role="MEMBER",
#         ).exists():
#             raise serializers.ValidationError("Member not found.")
#         return value
class GrantCreditsSerializer(serializers.Serializer):
    member_uuid = serializers.UUIDField()
    credits = serializers.IntegerField(min_value=1)
    expires_at = serializers.DateTimeField()

    def validate_expires_at(self, value):
        from django.utils import timezone

        if not timezone.is_aware(value):
            raise serializers.ValidationError(
                "Expiry date must include a timezone."
            )

        if value <= timezone.now():
            raise serializers.ValidationError(
                "Expiry date must be in the future."
            )

        return value

