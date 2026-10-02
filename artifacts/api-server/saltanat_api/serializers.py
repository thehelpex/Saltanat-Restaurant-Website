import re

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