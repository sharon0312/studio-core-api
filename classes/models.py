import uuid
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from studios.models import Studio
from django.contrib.auth.models import User
from users.models import UserDetail


class StudioClass(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=150)
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    spots = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    credit_cost = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.name} - {self.studio.name}"
    
    
    
class CreditPack(models.Model):
    member = models.ForeignKey(User,on_delete=models.PROTECT,related_name="credit_packs",)
    total_credits = models.PositiveIntegerField()
    remaining_credits = models.PositiveIntegerField()
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expires_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_credits__gt=0),
                name="credit_pack_total_gt_zero",
            ),
            models.CheckConstraint(
                condition=Q(remaining_credits__lte=F("total_credits")),
                name="credit_pack_remaining_lte_total",
            ),
        ]

    def __str__(self):
        return (
            f"{self.member_id}: "
            f"{self.remaining_credits}/{self.total_credits} credits"
        )




class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
    uuid = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    member = models.ForeignKey(User,on_delete=models.PROTECT,related_name="class_bookings",)
    studio_class = models.ForeignKey(StudioClass,on_delete=models.PROTECT,related_name="bookings",)
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.CONFIRMED,)
    credits_charged = models.PositiveIntegerField()
    idempotency_key = models.CharField(max_length=255,null=True,blank=True,)
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["member", "studio_class"],
                condition=Q(status="CONFIRMED"),
                name="unique_confirmed_member_class",
            ),
            models.UniqueConstraint(
                fields=["member", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="unique_booking_idempotency_key",
            ),
        ]


class WaitlistEntry(models.Model):
    member = models.ForeignKey(User,on_delete=models.PROTECT,related_name="class_waitlist_entries",)
    studio_class = models.ForeignKey(StudioClass,on_delete=models.PROTECT,related_name="waitlist_entries",)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "studio_class"],
                name="unique_waiting_member_class",
            )
        ]
