from django.shortcuts import render
from datetime import datetime

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from studio_core import helper
from users import models as user_models
from studios.models import Studio
from .models import StudioClass,CreditPack
from .serializers import StudioClassInputSerializer, StudioClassSerializer,StudioClassListSerializer,MembersListSerializer,GrantCreditsSerializer
from studio_core.helper import staff_required


# Create your views here.
@api_view(["POST"])
@staff_required
def create_class(request):
    serializer = StudioClassInputSerializer(data=request.data)
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST, "Invalid class data", serializer.errors)
    data = serializer.validated_data
    studio = Studio.objects.get(uuid=data.pop("studio_uuid"))
    studio_class = StudioClass.objects.create(studio=studio, **data)
    return helper.success(status.HTTP_201_CREATED, "Class created successfully", StudioClassSerializer(studio_class).data)


@api_view(["GET"])
@staff_required
def members_list(request):
    # serializer = StudioClassInputSerializer(data=request.data)
    # if not serializer.is_valid():
    #     return helper.failure(status.HTTP_400_BAD_REQUEST, "Invalid class data", serializer.errors)
    # data = serializer.validated_data
    members = user_models.UserDetail.objects.filter(role="MEMBER")
    print(members)
    serializer = MembersListSerializer(members,many=True)
    return helper.success(status.HTTP_201_CREATED, "Members fetched successfully",serializer.data)




# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def book_class(request):
#     serializer = StudioClassInputSerializer(data=request.data)
#     if not serializer.is_valid():
#         return helper.failure(status.HTTP_400_BAD_REQUEST, "Invalid class data", serializer.errors)
#     if not request.user.details.filter(role="MEMBER").exists():
#         return helper.failure(status.HTTP_403_FORBIDDEN, "Only members can book classes", {})
#     return helper.error(status.HTTP_501_NOT_IMPLEMENTED, "Booking requires the credit allocation service, which will be implemented next", {})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_classes(request):
    classes = StudioClass.objects.select_related("studio").all()
    serializer = StudioClassListSerializer(classes, many=True)
    return helper.success(status.HTTP_200_OK, "Classes fetched successfully", serializer.data)




@api_view(["POST"])
@staff_required
def grant_credits(request):
    serializer = GrantCreditsSerializer(data=request.data)
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST,"Invalid credit data",serializer.errors,)
    data = serializer.validated_data
    try:
        with transaction.atomic():
            # staff = user_models.UserDetail.objects.get(user=request.user,role="STAFF")
            member = user_models.UserDetail.objects.select_for_update().get(uuid=data["member_uuid"],role="MEMBER",)

            if data["expires_at"] <= timezone.now():
                return helper.failure(status.HTTP_400_BAD_REQUEST,"Expiry date must be in the future",)
            credit_pack = CreditPack.objects.create(
                member=member.user,
                total_credits=data["credits"],
                remaining_credits=data["credits"],
                expires_at=data["expires_at"],
            )

        return helper.success(status.HTTP_201_CREATED,
            "Credits granted successfully",
            {
                "member_uuid": str(member.uuid),
                "credit_pack_id": credit_pack.id,
                "credits_granted": credit_pack.total_credits,
                "remaining_credits": credit_pack.remaining_credits,
                "expires_at": credit_pack.expires_at,
            },
        )
    except user_models.UserDetail.DoesNotExist:
        return helper.failure(status.HTTP_404_NOT_FOUND,"Staff user or member not found")