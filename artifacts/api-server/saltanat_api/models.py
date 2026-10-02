import uuid

from django.db import models


class ReservationRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    phone = models.TextField()
    preferred_date = models.DateField()
    preferred_time = models.TextField()
    guest_count = models.IntegerField()
    notes = models.TextField(null=True, blank=True)
    status = models.TextField(default="awaiting_confirmation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "restaurant_reservation_requests"


class EventInquiry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    phone = models.TextField()
    email = models.TextField(null=True, blank=True)
    event_type = models.TextField()
    preferred_date = models.DateField(null=True, blank=True)
    guest_count = models.IntegerField()
    notes = models.TextField(null=True, blank=True)
    status = models.TextField(default="received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "restaurant_event_inquiries"