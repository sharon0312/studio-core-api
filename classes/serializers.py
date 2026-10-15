
from rest_framework import serializers
from .models import StudioClass,CreditPack,Booking,WaitlistEntry
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
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = StudioClass
        fields = ["uuid", "studio_uuid", "name", "start_time", "duration_minutes", "spots","available_spots","credit_cost", "created_at"]
        
    def get_available_spots(self, obj):
        booked_spots = Booking.objects.filter(
            studio_class=obj,
            status=Booking.Status.CONFIRMED,
        ).count()

        return max(obj.spots - booked_spots, 0)
    
    
class StudioClassListSerializer(serializers.ModelSerializer):
    # studio_uuid = serializers.UUIDField(source="studio.uuid", read_only=True)
    studio_name = serializers.CharField(source="studio.name", read_only=True)
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = StudioClass
        fields = ["uuid", "studio_name", "name", "start_time", "duration_minutes", "spots", "available_spots","credit_cost", "created_at"]
        
    def get_available_spots(self, obj):
        booked_spots = Booking.objects.filter(
            studio_class=obj,
            status=Booking.Status.CONFIRMED,
        ).count()

        return max(obj.spots - booked_spots, 0)

        
        
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


# class BookingRequestSerializer(serializers.Serializer):
#     class_uuid = serializers.SlugRelatedField(slug_field="uuid",queryset=StudioClass.objects.all(),source="studio_class",)
#     idempotency_key = serializers.CharField(max_length=255,allow_blank=False,trim_whitespace=True,)
#     def validate(self, attrs):
#         studio_class = attrs["studio_class"]
#         if studio_class.start_time <= timezone.now():
#             raise serializers.ValidationError({
#                 "class_uuid": "This class has already started."
#             })
#         return attrs


class BookingRequestSerializer(serializers.Serializer):
    class_uuid = serializers.UUIDField()
    idempotency_key = serializers.CharField(max_length=255,allow_blank=False,trim_whitespace=True,)
    
    
class BookingCancelInputSerializer(serializers.Serializer):
    booking_uuid = serializers.UUIDField()

class WaitingCancelInputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
    
class MyBookingListSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="studio_class.name",read_only=True,)
    studio_name = serializers.CharField(source="studio_class.studio.name",read_only=True,)
    start_time = serializers.DateTimeField(source="studio_class.start_time",read_only=True,)
    credit_cost = serializers.IntegerField(source="studio_class.credit_cost",read_only=True,)

    class Meta:
        model = Booking
        fields = ["uuid","class_name","studio_name","start_time","credit_cost","credits_charged","status","booked_at","cancelled_at",]


class WaitlistListSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="studio_class.name",read_only=True,)
    studio_name = serializers.CharField(source="studio_class.studio.name",read_only=True,)
    start_time = serializers.DateTimeField(source="studio_class.start_time",read_only=True,)
    credit_cost = serializers.IntegerField(source="studio_class.credit_cost",read_only=True,)

    class Meta:
        model = WaitlistEntry
        fields = ["id","class_name","studio_name","start_time","credit_cost","joined_at",]