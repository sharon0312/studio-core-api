from django.shortcuts import render
from datetime import datetime
from zoneinfo import ZoneInfo
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from studio_core import helper
from users import models as user_models
from studios.models import Studio
from .models import StudioClass,CreditPack,Booking,WaitlistEntry
from .serializers import StudioClassInputSerializer, StudioClassSerializer,StudioClassListSerializer,MembersListSerializer,GrantCreditsSerializer,BookingRequestSerializer,BookingCancelInputSerializer,WaitingCancelInputSerializer,WaitlistListSerializer,MyBookingListSerializer
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
    
    
@api_view(["POST"])
def book_class(request):
    # Validate the Idempotency-Key header.
    serializer = BookingRequestSerializer(
        data={
            "idempotency_key": request.headers.get("Idempotency-Key", ""),
            "class_uuid": request.data.get("class_uuid"),
        }
    )
    if not serializer.is_valid():
        return helper.failure(status.HTTP_400_BAD_REQUEST,"Invalid booking request",serializer.errors,)
    idempotency_key = serializer.validated_data["idempotency_key"]
    class_uuid = serializer.validated_data["class_uuid"]
    is_member = user_models.UserDetail.objects.filter(user=request.user,role="MEMBER",).exists()
    if not is_member:
        return helper.failure(status.HTTP_403_FORBIDDEN,"Member access required",)
    try:
        with transaction.atomic():
            studio_class = (
                StudioClass.objects
                .select_for_update()
                .get(uuid=class_uuid)
            )
            # Return the result if this key was already processed.
            existing_booking = Booking.objects.filter(member=request.user,idempotency_key=idempotency_key,).first()

            if existing_booking:
                if existing_booking.studio_class_id != studio_class.pk:
                    return helper.failure(status.HTTP_400_BAD_REQUEST,"Idempotency-Key was already used for another class",)
                return helper.success(status.HTTP_200_OK,
                    "Booking request already processed",
                    {
                        "booking_id": existing_booking.pk,
                        "status": existing_booking.status,
                    },
                )

            if studio_class.start_time <= timezone.now():
                return helper.failure(status.HTTP_400_BAD_REQUEST,"Class has already started",)

            if Booking.objects.filter(
                member=request.user,
                studio_class=studio_class,
                status=Booking.Status.CONFIRMED,
            ).exists():
                return helper.failure(status.HTTP_400_BAD_REQUEST,"You already have a confirmed booking",)
            if WaitlistEntry.objects.filter(
                member=request.user,
                studio_class=studio_class,
            ).exists():
                return helper.success(status.HTTP_200_OK,"You are already on the waitlist",{"status": "WAITING"},)
            confirmed_count = Booking.objects.filter(studio_class=studio_class,status=Booking.Status.CONFIRMED,).count()

            if confirmed_count >= studio_class.spots:
                entry = WaitlistEntry.objects.create(member=request.user,studio_class=studio_class)

                return helper.success(
                    status.HTTP_201_CREATED,"Class is full. Added to waitlist",
                    {
                        "waitlist_id": entry.pk,
                        "status": "WAITING",
                        "credits_charged": 0,
                    },
                )

            packs = list(
                CreditPack.objects.select_for_update().filter(member=request.user,remaining_credits__gt=0,expires_at__gt=timezone.now(),
                ).order_by("expires_at", "granted_at", "pk")
            )

            available_credits = sum(
                pack.remaining_credits for pack in packs
            )
            cost = studio_class.credit_cost

            if available_credits < cost:
                return helper.failure(
                    status.HTTP_400_BAD_REQUEST,
                    "Insufficient credits",
                    {
                        "required_credits": cost,
                        "available_credits": available_credits,
                    },
                )

            remaining_cost = cost

            for pack in packs:
                if remaining_cost <= 0:
                    break

                deduction = min(pack.remaining_credits, remaining_cost)
                pack.remaining_credits -= deduction
                pack.save(update_fields=["remaining_credits"])
                remaining_cost -= deduction

            booking = Booking.objects.create(
                member=request.user,
                studio_class=studio_class,
                status=Booking.Status.CONFIRMED,
                credits_charged=cost,
                idempotency_key=idempotency_key,
            )
            data = {
                    "booking_id": booking.pk,
                    "status": booking.status,
                    "credits_charged": cost,
                    "remaining_credits": available_credits - cost,
                }

            return helper.success(status.HTTP_201_CREATED,"Class booked successfully",data)

    except StudioClass.DoesNotExist:
        return helper.failure(status.HTTP_404_NOT_FOUND,"Class not found")
    
def promote_waitlisted_member(studio_class):
    now = timezone.now()
    waiting_entries = (
        WaitlistEntry.objects
        .select_for_update()
        .filter(studio_class=studio_class)
        .order_by("joined_at", "id")
    )
    for entry in waiting_entries:
        credit_packs = list(
            CreditPack.objects
            .select_for_update()
            .filter(
                member=entry.member,
                expires_at__gt=now,
                remaining_credits__gt=0,
            )
            .order_by("expires_at", "id")
        )
        available_credits = sum(
            pack.remaining_credits for pack in credit_packs
        )
        if available_credits < studio_class.credit_cost:
            continue
        credits_needed = studio_class.credit_cost
        for pack in credit_packs:
            deduction = min(pack.remaining_credits, credits_needed)
            pack.remaining_credits -= deduction
            pack.save(update_fields=["remaining_credits"])
            credits_needed -= deduction
            if credits_needed == 0:
                break
        booking = Booking.objects.create(
            member=entry.member,
            studio_class=studio_class,
            status=Booking.Status.CONFIRMED,
            credits_charged=studio_class.credit_cost,
        )
        entry.delete()
        return booking
    return None
    
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    with transaction.atomic():
        print(request.user.id)
        serializer =  BookingCancelInputSerializer(data=request.data)
        if not serializer.is_valid():
            return helper.failure(status.HTTP_400_BAD_REQUEST,"Invalid booking request",serializer.errors,)
        booking_id = serializer.validated_data['booking_uuid']
        booking = ( Booking.objects.select_for_update().select_related("studio_class__studio").filter(uuid=booking_id,member=request.user,).first())
        if not booking:
            return helper.failure(status.HTTP_404_NOT_FOUND,"Booking not found",)
        if booking.status == Booking.Status.CANCELLED:
            return helper.failure(status.HTTP_400_BAD_REQUEST,"Booking has already been cancelled",)
        studio_class = booking.studio_class
        studio = studio_class.studio
        # Convert the class start time to the studio's local timezone.
        studio_timezone = ZoneInfo(studio.timezone)
        class_start = studio_class.start_time.astimezone(studio_timezone)
        cancellation_cutoff = (
            class_start - timezone.timedelta(hours=studio.cancellation_cutoff_hours)
        )
        current_time = timezone.now().astimezone(studio_timezone)
        eligible_for_refund = current_time <= cancellation_cutoff
        if eligible_for_refund:
            credit_pack = CreditPack.objects.filter(member=booking.member,expires_at__gt=timezone.now(),).order_by("expires_at", "id").first()
            if credit_pack:
                credit_pack.remaining_credits += booking.studio_class.credit_cost
                credit_pack.total_credits += booking.studio_class.credit_cost
                credit_pack.save(update_fields=["remaining_credits", "total_credits"])
        booking.status = Booking.Status.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=["status", "cancelled_at"])
        promoted_booking = promote_waitlisted_member(studio_class)
    return helper.success(
        status.HTTP_200_OK,
        (
            "Booking cancelled and credits refunded"
            if eligible_for_refund
            else "Booking cancelled; credits forfeited"
        ),
        {
            "booking_id": booking.id,
            "status": booking.status,
            "credits_refunded": (
                booking.credits_charged if eligible_for_refund else 0
            ),
        },
    )
    
    
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def leave_waitlist(request):
    with transaction.atomic():
        serializer =  WaitingCancelInputSerializer(data=request.data)
        if not serializer.is_valid():
            return helper.failure(status.HTTP_400_BAD_REQUEST,"Invalid cancel request",serializer.errors,)
        waitlist_id = serializer.validated_data['waitlist_id']
        entry = (
            WaitlistEntry.objects
            .select_for_update()
            .filter(id=waitlist_id,member=request.user,).first()
        )
        if not entry:
            return helper.failure(status.HTTP_404_NOT_FOUND,"Waitlist entry not found",)
        entry.delete()
    return helper.success(status.HTTP_200_OK,"Successfully left the waitlist",[])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    bookings = (Booking.objects.filter(member=request.user).select_related("studio_class__studio").order_by("-booked_at"))
    serializer = MyBookingListSerializer(bookings, many=True)
    return helper.success(status.HTTP_200_OK,"Bookings fetched successfully",serializer.data,)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_waitlist(request):
    waitlist_entries = (WaitlistEntry.objects.filter(member=request.user).select_related("studio_class__studio").order_by("joined_at", "id"))
    serializer = WaitlistListSerializer(waitlist_entries,many=True,)
    return helper.success(status.HTTP_200_OK,"Waitlist fetched successfully",serializer.data,)