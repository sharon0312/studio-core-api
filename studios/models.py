# Create your models here.
from django.core.validators import MinValueValidator
from django.db import models
from studio_core.helper import validate_timezone
import uuid


class Studio(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    name = models.CharField(max_length=150)
    timezone = models.CharField(max_length=64,default="Asia/Kolkata",validators=[validate_timezone])
    cancellation_cutoff_hours = models.PositiveIntegerField(default=4,validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
