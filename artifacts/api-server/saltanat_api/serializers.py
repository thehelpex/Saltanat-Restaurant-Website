import re
from urllib.parse import urlsplit

from rest_framework import serializers


class MenuFilterSerializer(serializers.Serializer):
    category = serializers.CharField(required=False, allow_blank=True)
    search = serializers.CharField(required=False, allow_blank=True)


class MenuItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    pricePkr = serializers.IntegerField()
    imageUrl = serializers.CharField(allow_null=True)
    isFeatured = serializers.BooleanField()
    isAvailable = serializers.BooleanField()


class MenuCategoryAdminSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(min_length=2, max_length=80)
    sortOrder = serializers.IntegerField(source="sort_order", required=False, min_value=0)
    isActive = serializers.BooleanField(source="is_active", required=False)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter a category name.")
        return value


class MenuItemAdminSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(min_length=2, max_length=120)
    categoryId = serializers.IntegerField(source="category_id", min_value=1)
    categoryName = serializers.CharField(source="category.name", read_only=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=1000)
    pricePkr = serializers.IntegerField(source="price_pkr", min_value=0, max_value=1000000)
    imageUrl = serializers.CharField(source="image_url", required=False, allow_null=True, allow_blank=True, max_length=500)
    isFeatured = serializers.BooleanField(source="is_featured", required=False)
    isAvailable = serializers.BooleanField(source="is_available", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    sortOrder = serializers.IntegerField(source="sort_order", required=False, min_value=0)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter a menu item name.")
        return value

    def validate(self, attrs):
        image_url = attrs.get("image_url")
        if image_url:
            try:
                parsed_url = urlsplit(image_url)
            except ValueError as error:
                raise serializers.ValidationError(
                    {"imageUrl": "Use a site-relative path or secure HTTPS image URL."}
                ) from error
            is_site_path = (
                image_url.startswith("/")
                and not image_url.startswith("//")
                and "\\" not in image_url
                and not parsed_url.netloc
                and not parsed_url.scheme
            )
            is_secure_url = (
                parsed_url.scheme == "https"
                and bool(parsed_url.netloc)
                and not parsed_url.username
                and not parsed_url.password
            )
            if not (is_site_path or is_secure_url):
                raise serializers.ValidationError(
                    {"imageUrl": "Use a site-relative path or secure HTTPS image URL."}
                )
        return attrs


class DeliveryAreaAdminSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(min_length=2, max_length=120)
    deliveryFeePkr = serializers.IntegerField(source="delivery_fee_pkr", min_value=0, max_value=100000)
    isActive = serializers.BooleanField(source="is_active", required=False)
    sortOrder = serializers.IntegerField(source="sort_order", required=False, min_value=0)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter a delivery area name.")
        return value


class RestaurantRequestUpdateSerializer(serializers.Serializer):
    status = serializers.CharField()

    def validate_status(self, value):
        allowed_statuses = self.context.get("allowed_statuses", ())
        if value not in allowed_statuses:
            raise serializers.ValidationError("Choose a valid request status.")
        return value


class ReservationInputSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=120)
    phone = serializers.CharField(min_length=7, max_length=30)
    preferredDate = serializers.DateField(source="preferred_date", input_formats=["%Y-%m-%d"])
    preferredTime = serializers.RegexField(
        r"^([01]\d|2[0-3]):[0-5]\d$",
        source="preferred_time",
    )
    guestCount = serializers.IntegerField(source="guest_count", min_value=1, max_value=50)
    notes = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=1000,
    )

    def validate_phone(self, value):
        if len(re.sub(r"\D", "", value)) < 7:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value


class EventInquiryInputSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=120)
    phone = serializers.CharField(min_length=7, max_length=30)
    email = serializers.EmailField(
        required=True,
        allow_null=True,
        allow_blank=True,
        max_length=254,
    )
    eventType = serializers.ChoiceField(
        source="event_type",
        choices=["birthday", "corporate", "family-gathering", "other"],
    )
    preferredDate = serializers.DateField(
        source="preferred_date",
        required=True,
        allow_null=True,
        input_formats=["%Y-%m-%d"],
    )
    guestCount = serializers.IntegerField(source="guest_count", min_value=1, max_value=500)
    notes = serializers.CharField(
        required=True,
        allow_null=True,
        allow_blank=True,
        max_length=2000,
    )

    def validate_phone(self, value):
        if len(re.sub(r"\D", "", value)) < 7:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_email(self, value):
        return value.strip() or None if value is not None else None


class RestaurantOrderItemInputSerializer(serializers.Serializer):
    menuItemId = serializers.IntegerField(source="menu_item_id", min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class RestaurantOrderInputSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=120)
    phone = serializers.CharField(min_length=7, max_length=30)
    fulfillmentType = serializers.ChoiceField(
        source="fulfillment_type",
        choices=["pickup", "delivery"],
    )
    deliveryAddress = serializers.CharField(
        source="delivery_address",
        required=False,
        allow_blank=True,
        max_length=500,
    )
    deliveryAreaId = serializers.IntegerField(
        source="delivery_area_id",
        required=False,
        min_value=1,
    )
    paymentMethod = serializers.ChoiceField(
        source="payment_method",
        choices=["cod", "card"],
    )
    notes = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=1000,
    )
    items = RestaurantOrderItemInputSerializer(
        many=True,
        allow_empty=False,
        max_length=50,
    )

    def validate_phone(self, value):
        if len(re.sub(r"\D", "", value)) < 7:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate(self, attrs):
        if attrs["fulfillment_type"] == "delivery" and not attrs.get(
            "delivery_address", ""
        ).strip():
            raise serializers.ValidationError(
                {"deliveryAddress": "A delivery address is required."}
            )
        return attrs


class StaffOrderUpdateSerializer(serializers.Serializer):
    orderStatus = serializers.ChoiceField(
        source="order_status",
        required=False,
        choices=[
            "confirmed",
            "preparing",
            "ready",
            "completed",
            "cancelled",
        ],
    )
    paymentStatus = serializers.ChoiceField(
        source="payment_status",
        required=False,
        choices=["unpaid", "paid"],
    )
    deliveryFeePkr = serializers.IntegerField(
        source="delivery_fee_pkr",
        required=False,
        min_value=0,
        max_value=100000,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one order update.")
        return attrs