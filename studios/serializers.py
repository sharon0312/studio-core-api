from rest_framework import serializers
from .models import Studio
from studio_core.helper import validate_timezone

class StudioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ["uuid","name","timezone","cancellation_cutoff_hours","created_at","updated_at"]
        
        
class StudioDetailInputSerializer(serializers.Serializer):
    studio_id = serializers.UUIDField()
    
    
class CreateStudioInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    timezone = serializers.CharField(max_length=64,default="Asia/Kolkata",validators=[validate_timezone],)
    cancellation_cutoff_hours = serializers.IntegerField(default=4,min_value=0,)