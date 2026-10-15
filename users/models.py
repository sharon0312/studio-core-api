from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

class UserDetail(models.Model):
    class Role(models.TextChoices):
        STAFF = "STAFF", "Staff"
        MEMBER = "MEMBER", "Member"
    uuid = models.UUIDField(default=uuid4, unique=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="details",)
    role = models.CharField(max_length=10,choices=Role.choices,default=Role.MEMBER,)
    phone_code = models.CharField(max_length=7,blank=True,)
    phone_number = models.CharField(max_length=20,blank=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["phone_code", "phone_number"],
                name="unique_phone_code_number",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"
    
    
class UserOTP(models.Model):
    phone_number = models.CharField(max_length=40,null=True,blank=True)
    otp = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

