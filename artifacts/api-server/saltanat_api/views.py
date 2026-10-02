import json
from pathlib import Path

from django.http import HttpRequest
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import EventInquiry, ReservationRequest
from .serializers import (
    EventInquiryInputSerializer,
    MenuFilterSerializer,
    MenuItemSerializer,
    ReservationInputSerializer,
)


MENU_ITEMS = json.loads(Path(__file__).resolve().parent.parent.joinpath("menu_data.json").read_text())


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(_request: HttpRequest):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def list_restaurant_menu(request: HttpRequest):
    filters = MenuFilterSerializer(data=request.query_params)
    if not filters.is_valid():
        return Response({"error": "Invalid menu filters."}, status=status.HTTP_400_BAD_REQUEST)

    category = filters.validated_data.get("category", "").strip().casefold()
    search = filters.validated_data.get("search", "").strip().casefold()
    filtered = [
        item
        for item in MENU_ITEMS
        if (not category or category == "all" or item["category"].casefold() == category)
        and (
            not search
            or search
            in f'{item["name"]} {item["category"]} {item["description"] or ""}'.casefold()
        )
    ]
    return Response(MenuItemSerializer(filtered, many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def create_reservation_request(request: HttpRequest):
    serializer = ReservationInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Please check the reservation details and try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    reservation = ReservationRequest.objects.create(
        **{
            **data,
            "name": data["name"].strip(),
            "phone": data["phone"].strip(),
            "notes": (data.get("notes") or "").strip() or None,
            "status": "awaiting_confirmation",
        }
    )
    return Response(
        {
            "id": str(reservation.id),
            "status": "awaiting_confirmation",
            "message": (
                "Your request has been recorded. Please call Saltanat to confirm availability; "
                "this is not a confirmed reservation."
            ),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_event_inquiry(request: HttpRequest):
    serializer = EventInquiryInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Please check the event details and try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    inquiry = EventInquiry.objects.create(
        **{
            **data,
            "name": data["name"].strip(),
            "phone": data["phone"].strip(),
            "email": (data.get("email") or "").strip() or None,
            "notes": (data.get("notes") or "").strip() or None,
            "status": "received",
        }
    )
    return Response(
        {
            "id": str(inquiry.id),
            "status": "received",
            "message": (
                "Your inquiry has been recorded. Please call Saltanat to discuss availability "
                "and arrangements."
            ),
        },
        status=status.HTTP_201_CREATED,
    )