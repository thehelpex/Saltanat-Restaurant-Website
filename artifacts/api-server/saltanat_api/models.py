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


class RestaurantMenuCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField(unique=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "restaurant_menu_categories"


class RestaurantMenuItem(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(
        RestaurantMenuCategory,
        db_column="category_id",
        on_delete=models.PROTECT,
        related_name="items",
    )
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    price_pkr = models.IntegerField()
    image_url = models.TextField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "restaurant_menu_items"


class RestaurantDeliveryArea(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField(unique=True)
    delivery_fee_pkr = models.IntegerField()
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "restaurant_delivery_areas"


class RestaurantOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.TextField()
    phone = models.TextField()
    fulfillment_type = models.TextField()
    delivery_address = models.TextField(null=True, blank=True)
    delivery_area = models.TextField(null=True, blank=True)
    delivery_area_ref = models.ForeignKey(
        RestaurantDeliveryArea,
        db_column="delivery_area_id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    payment_method = models.TextField()
    order_status = models.TextField(default="awaiting_confirmation")
    payment_status = models.TextField(default="unpaid")
    subtotal_pkr = models.IntegerField()
    delivery_fee_pkr = models.IntegerField(null=True, blank=True)
    total_pkr = models.IntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "restaurant_orders"


class RestaurantOrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        RestaurantOrder,
        db_column="order_id",
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item_id = models.IntegerField()
    item_name = models.TextField()
    quantity = models.IntegerField()
    unit_price_pkr = models.IntegerField()

    class Meta:
        managed = False
        db_table = "restaurant_order_items"


class RestaurantOrderAudit(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        RestaurantOrder,
        db_column="order_id",
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    actor = models.TextField()
    action = models.TextField()
    previous_order_status = models.TextField()
    new_order_status = models.TextField()
    previous_payment_status = models.TextField()
    new_payment_status = models.TextField()
    previous_delivery_fee_pkr = models.IntegerField(null=True, blank=True)
    new_delivery_fee_pkr = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "restaurant_order_audit"


class RestaurantOrderNotification(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        RestaurantOrder,
        db_column="order_id",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    channel = models.TextField()
    status = models.TextField(default="pending")
    attempt_count = models.IntegerField(default=0)
    available_at = models.DateTimeField()
    locked_until = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    delivered_recipients = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "restaurant_order_notifications"