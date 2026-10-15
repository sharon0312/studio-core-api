from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from studio_core import helper
from .models import Studio
from studios.serializers import StudioListSerializer,StudioDetailInputSerializer,CreateStudioInputSerializer
from studio_core.helper import staff_required


@api_view(['GET'])
def list_studios(request):
    studios = Studio.objects.all()
    serializer = StudioListSerializer(studios, many=True)
    return helper.success(status.HTTP_200_OK, "Studios fetched successfully",serializer.data)


@api_view(['GET'])
def studio_detail(request):
    serializer = StudioDetailInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST,helper.get_serializer_first_error(serializer))
    studio_id = serializer.validated_data['studio_id']
    try:
        studio = Studio.objects.get(uuid=studio_id)
    except Studio.DoesNotExist:
            return helper.failure(status.HTTP_400_BAD_REQUEST,"Studio not found",error=[])
    serializer = StudioListSerializer(studio)
    return helper.success(status.HTTP_200_OK, "Studios fetched successfully",serializer.data)

  
  
  
@api_view(['POST'])
@staff_required
def create_studio(request):
    serializer = CreateStudioInputSerializer(data=request.data)
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST,"Invalid studio data",serializer.errors,)
    validated_data = serializer.validated_data
    studio = Studio.objects.create(
        name=validated_data["name"],
        timezone=validated_data.get("timezone", "Asia/Kolkata"),
        cancellation_cutoff_hours=validated_data.get(
            "cancellation_cutoff_hours", 4
        ),
    )
    return helper.success(status.HTTP_201_CREATED,"Studio created successfully",StudioListSerializer(studio).data,)
