import logging
from uuid import uuid4

from django.db import DatabaseError, connection, transaction
from django.http import HttpRequest
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    EventInquiry,
    ReservationRequest,
    RestaurantDeliveryArea,
    RestaurantMenuCategory,
    RestaurantMenuItem,
    RestaurantOrder,
    RestaurantOrderAudit,
    RestaurantOrderItem,
    RestaurantOrderNotification,
)
from .payments import PaymentGatewayNotConfigured, get_hosted_payment_gateway
from .serializers import (
    EventInquiryInputSerializer,
    DeliveryAreaAdminSerializer,
    MenuFilterSerializer,
    MenuCategoryAdminSerializer,
    MenuItemAdminSerializer,
    MenuItemSerializer,
    ReservationInputSerializer,
    RestaurantOrderInputSerializer,
    RestaurantRequestUpdateSerializer,
    StaffOrderUpdateSerializer,
)
from .staff_auth import staff_actor
from .throttling import (
    EventInquiryCreationThrottle,
    OrderCreationThrottle,
    ReservationCreationThrottle,
    StaffApiThrottle,
)


order_logger = logging.getLogger("saltanat.orders")


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(_request: HttpRequest):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        order_logger.exception("API health check failed: database unavailable")
        return Response(
            {"status": "unavailable", "database": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response({"status": "ok", "database": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def list_restaurant_menu(request: HttpRequest):
    filters = MenuFilterSerializer(data=request.query_params)
    if not filters.is_valid():
        return Response({"error": "Invalid menu filters."}, status=status.HTTP_400_BAD_REQUEST)

    category = filters.validated_data.get("category", "").strip().casefold()
    search = filters.validated_data.get("search", "").strip().casefold()
    filtered = _available_menu_items()
    filtered = [
        item
        for item in filtered
        if (not category or category == "all" or item["category"].casefold() == category)
        and (
            not search
            or search
            in f'{item["name"]} {item["category"]} {item["description"] or ""}'.casefold()
        )
    ]
    return Response(MenuItemSerializer(filtered, many=True).data)


def _available_menu_items() -> list[dict]:
    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category.name,
            "description": item.description,
            "pricePkr": item.price_pkr,
            "imageUrl": item.image_url,
            "isFeatured": item.is_featured,
            "isAvailable": item.is_available,
        }
        for item in RestaurantMenuItem.objects.select_related("category")
        .filter(is_active=True, category__is_active=True)
        .order_by("category__sort_order", "sort_order", "name")
    ]


def _orderable_menu_items(item_ids: set[int]) -> dict[int, RestaurantMenuItem]:
    return {
        item.id: item
        for item in RestaurantMenuItem.objects.select_for_update()
        .select_related("category")
        .filter(
            id__in=item_ids,
            is_active=True,
            is_available=True,
            category__is_active=True,
        )
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def list_delivery_areas(request: HttpRequest):
    areas = RestaurantDeliveryArea.objects.filter(is_active=True).order_by(
        "sort_order", "name"
    )
    return Response(DeliveryAreaAdminSerializer(areas, many=True).data)


def _manager_auth_error(request: HttpRequest):
    _actor, error = staff_actor(request)
    return error


@api_view(["GET", "POST"])
@throttle_classes([StaffApiThrottle])
def manager_categories(request: HttpRequest):
    error = _manager_auth_error(request)
    if error:
        return error

    if request.method == "GET":
        categories = RestaurantMenuCategory.objects.order_by("sort_order", "name")
        return Response(MenuCategoryAdminSerializer(categories, many=True).data)

    serializer = MenuCategoryAdminSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Check the category details."}, status=400)
    values = serializer.validated_data
    name = values["name"].strip()
    if RestaurantMenuCategory.objects.filter(name__iexact=name).exists():
        return Response({"error": "A category with that name already exists."}, status=409)
    category = RestaurantMenuCategory.objects.create(
        name=name,
        sort_order=values.get("sort_order", 0),
        is_active=values.get("is_active", True),
    )
    return Response(MenuCategoryAdminSerializer(category).data, status=201)


@api_view(["PATCH", "DELETE"])
@throttle_classes([StaffApiThrottle])
def manager_category_detail(request: HttpRequest, category_id: int):
    error = _manager_auth_error(request)
    if error:
        return error
    try:
        category = RestaurantMenuCategory.objects.get(id=category_id)
    except RestaurantMenuCategory.DoesNotExist:
        return Response({"error": "Category not found."}, status=404)

    if request.method == "DELETE":
        category.is_active = False
        category.save(update_fields=["is_active"])
        return Response(status=204)

    serializer = MenuCategoryAdminSerializer(category, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({"error": "Check the category details."}, status=400)
    values = serializer.validated_data
    name = values.get("name")
    if name and RestaurantMenuCategory.objects.filter(name__iexact=name).exclude(
        id=category.id
    ).exists():
        return Response({"error": "A category with that name already exists."}, status=409)
    for field, value in values.items():
        setattr(category, field, value.strip() if field == "name" else value)
    category.save(update_fields=list(values))
    return Response(MenuCategoryAdminSerializer(category).data)


@api_view(["GET", "POST"])
@throttle_classes([StaffApiThrottle])
def manager_menu_items(request: HttpRequest):
    error = _manager_auth_error(request)
    if error:
        return error

    if request.method == "GET":
        items = RestaurantMenuItem.objects.select_related("category").order_by(
            "category__sort_order", "sort_order", "name"
        )
        return Response(MenuItemAdminSerializer(items, many=True).data)

    serializer = MenuItemAdminSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Check the menu item details."}, status=400)
    values = serializer.validated_data
    if "id" in request.data:
        return Response({"error": "Menu item IDs are assigned by the server."}, status=400)
    try:
        category = RestaurantMenuCategory.objects.get(
            id=values["category_id"], is_active=True
        )
    except RestaurantMenuCategory.DoesNotExist:
        return Response({"error": "Choose an active menu category."}, status=400)
    name = values["name"].strip()
    if RestaurantMenuItem.objects.filter(name__iexact=name, is_active=True).exists():
        return Response({"error": "An active menu item with that name already exists."}, status=409)
    item = RestaurantMenuItem.objects.create(
        category=category,
        name=name,
        description=(values.get("description") or "").strip() or None,
        price_pkr=values["price_pkr"],
        image_url=values.get("image_url"),
        is_featured=values.get("is_featured", False),
        is_available=values.get("is_available", True),
        is_active=values.get("is_active", True),
        sort_order=values.get("sort_order", 0),
    )
    return Response(MenuItemAdminSerializer(item).data, status=201)


@api_view(["PATCH", "DELETE"])
@throttle_classes([StaffApiThrottle])
def manager_menu_item_detail(request: HttpRequest, item_id: int):
    error = _manager_auth_error(request)
    if error:
        return error
    try:
        item = RestaurantMenuItem.objects.select_related("category").get(id=item_id)
    except RestaurantMenuItem.DoesNotExist:
        return Response({"error": "Menu item not found."}, status=404)

    if request.method == "DELETE":
        item.is_active = False
        item.save(update_fields=["is_active"])
        return Response(status=204)

    serializer = MenuItemAdminSerializer(item, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({"error": "Check the menu item details."}, status=400)
    values = serializer.validated_data
    if "category_id" in values:
        try:
            values["category"] = RestaurantMenuCategory.objects.get(
                id=values.pop("category_id"), is_active=True
            )
        except RestaurantMenuCategory.DoesNotExist:
            return Response({"error": "Choose an active menu category."}, status=400)
    if "name" in values:
        values["name"] = values["name"].strip()
        if RestaurantMenuItem.objects.filter(
            name__iexact=values["name"], is_active=True
        ).exclude(id=item.id).exists():
            return Response({"error": "An active menu item with that name already exists."}, status=409)
    if "description" in values:
        values["description"] = (values["description"] or "").strip() or None
    for field, value in values.items():
        setattr(item, field, value)
    item.save(update_fields=list(values))
    return Response(MenuItemAdminSerializer(item).data)


@api_view(["GET", "POST"])
@throttle_classes([StaffApiThrottle])
def manager_delivery_areas(request: HttpRequest):
    error = _manager_auth_error(request)
    if error:
        return error

    if request.method == "GET":
        areas = RestaurantDeliveryArea.objects.order_by("sort_order", "name")
        return Response(DeliveryAreaAdminSerializer(areas, many=True).data)

    serializer = DeliveryAreaAdminSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Check the delivery area details."}, status=400)
    values = serializer.validated_data
    name = values["name"].strip()
    if RestaurantDeliveryArea.objects.filter(name__iexact=name).exists():
        return Response({"error": "A delivery area with that name already exists."}, status=409)
    area = RestaurantDeliveryArea.objects.create(
        name=name,
        delivery_fee_pkr=values["delivery_fee_pkr"],
        is_active=values.get("is_active", True),
        sort_order=values.get("sort_order", 0),
    )
    return Response(DeliveryAreaAdminSerializer(area).data, status=201)


@api_view(["PATCH", "DELETE"])
@throttle_classes([StaffApiThrottle])
def manager_delivery_area_detail(request: HttpRequest, area_id: int):
    error = _manager_auth_error(request)
    if error:
        return error
    try:
        area = RestaurantDeliveryArea.objects.get(id=area_id)
    except RestaurantDeliveryArea.DoesNotExist:
        return Response({"error": "Delivery area not found."}, status=404)

    if request.method == "DELETE":
        area.is_active = False
        area.save(update_fields=["is_active"])
        return Response(status=204)

    serializer = DeliveryAreaAdminSerializer(area, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({"error": "Check the delivery area details."}, status=400)
    values = serializer.validated_data
    name = values.get("name")
    if name and RestaurantDeliveryArea.objects.filter(name__iexact=name).exclude(
        id=area.id
    ).exists():
        return Response({"error": "A delivery area with that name already exists."}, status=409)
    for field, value in values.items():
        setattr(area, field, value.strip() if field == "name" else value)
    area.save(update_fields=list(values))
    return Response(DeliveryAreaAdminSerializer(area).data)


@api_view(["GET"])
@throttle_classes([StaffApiThrottle])
def manager_reservations(request: HttpRequest):
    error = _manager_auth_error(request)
    if error:
        return error
    reservations = ReservationRequest.objects.order_by("-created_at")[:200]
    return Response(
        [
            {
                "id": str(row.id),
                "name": row.name,
                "phone": row.phone,
                "preferredDate": row.preferred_date.isoformat(),
                "preferredTime": row.preferred_time,
                "guestCount": row.guest_count,
                "notes": row.notes,
                "status": row.status,
                "createdAt": row.created_at.isoformat(),
            }
            for row in reservations
        ]
    )


@api_view(["PATCH"])
@throttle_classes([StaffApiThrottle])
def manager_reservation_detail(request: HttpRequest, reservation_id):
    error = _manager_auth_error(request)
    if error:
        return error
    serializer = RestaurantRequestUpdateSerializer(
        data=request.data,
        context={
            "allowed_statuses": [
                "awaiting_confirmation",
                "confirmed",
                "declined",
                "cancelled",
            ]
        },
    )
    if not serializer.is_valid():
        return Response({"error": "Choose a valid reservation status."}, status=400)
    try:
        reservation = ReservationRequest.objects.get(id=reservation_id)
    except ReservationRequest.DoesNotExist:
        return Response({"error": "Reservation not found."}, status=404)
    reservation.status = serializer.validated_data["status"]
    reservation.save(update_fields=["status"])
    return Response({"id": str(reservation.id), "status": reservation.status})


@api_view(["GET"])
@throttle_classes([StaffApiThrottle])
def manager_event_inquiries(request: HttpRequest):
    error = _manager_auth_error(request)
    if error:
        return error
    inquiries = EventInquiry.objects.order_by("-created_at")[:200]
    return Response(
        [
            {
                "id": str(row.id),
                "name": row.name,
                "phone": row.phone,
                "email": row.email,
                "eventType": row.event_type,
                "preferredDate": row.preferred_date.isoformat() if row.preferred_date else None,
                "guestCount": row.guest_count,
                "notes": row.notes,
                "status": row.status,
                "createdAt": row.created_at.isoformat(),
            }
            for row in inquiries
        ]
    )


@api_view(["PATCH"])
@throttle_classes([StaffApiThrottle])
def manager_event_inquiry_detail(request: HttpRequest, inquiry_id):
    error = _manager_auth_error(request)
    if error:
        return error
    serializer = RestaurantRequestUpdateSerializer(
        data=request.data,
        context={"allowed_statuses": ["received", "contacted", "completed", "declined"]},
    )
    if not serializer.is_valid():
        return Response({"error": "Choose a valid inquiry status."}, status=400)
    try:
        inquiry = EventInquiry.objects.get(id=inquiry_id)
    except EventInquiry.DoesNotExist:
        return Response({"error": "Event inquiry not found."}, status=404)
    inquiry.status = serializer.validated_data["status"]
    inquiry.save(update_fields=["status"])
    return Response({"id": str(inquiry.id), "status": inquiry.status})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ReservationCreationThrottle])
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
@throttle_classes([EventInquiryCreationThrottle])
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


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([OrderCreationThrottle])
def create_restaurant_order(request: HttpRequest):
    serializer = RestaurantOrderInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Please check your order details and try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    requested_items = data["items"]
    requested_ids = {item["menu_item_id"] for item in requested_items}
    order_id = uuid4()

    with transaction.atomic():
        menu_by_id = _orderable_menu_items(requested_ids)
        if requested_ids != set(menu_by_id):
            return Response(
                {"error": "One or more selected menu items are no longer available. Refresh the menu and try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subtotal = sum(
            menu_by_id[item["menu_item_id"]].price_pkr * item["quantity"]
            for item in requested_items
        )
        if data["payment_method"] == "card":
            try:
                get_hosted_payment_gateway()
            except PaymentGatewayNotConfigured:
                return Response(
                    {"error": "Online card payment is not configured yet. Please choose cash on delivery."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return Response(
                {"error": "Online card checkout is not enabled for this site yet."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        is_delivery = data["fulfillment_type"] == "delivery"
        delivery_area = None
        if is_delivery:
            area_id = data.get("delivery_area_id")
            if area_id is None:
                return Response(
                    {"error": "Choose a delivery area to calculate its delivery fee."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                delivery_area = RestaurantDeliveryArea.objects.select_for_update().get(
                    id=area_id, is_active=True
                )
            except RestaurantDeliveryArea.DoesNotExist:
                return Response(
                    {"error": "That delivery area is not currently available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        order = RestaurantOrder.objects.create(
            id=order_id,
            customer_name=data["name"].strip(),
            phone=data["phone"].strip(),
            fulfillment_type=data["fulfillment_type"],
            delivery_address=(data.get("delivery_address") or "").strip() or None,
            delivery_area=delivery_area.name if delivery_area else None,
            delivery_area_ref=delivery_area,
            payment_method="cod",
            order_status="awaiting_confirmation",
            payment_status="unpaid",
            subtotal_pkr=subtotal,
            delivery_fee_pkr=delivery_area.delivery_fee_pkr if delivery_area else 0,
            total_pkr=subtotal + delivery_area.delivery_fee_pkr if delivery_area else subtotal,
            notes=(data.get("notes") or "").strip() or None,
        )
        RestaurantOrderItem.objects.bulk_create(
            [
                RestaurantOrderItem(
                    order=order,
                    menu_item_id=item["menu_item_id"],
                    item_name=menu_by_id[item["menu_item_id"]].name,
                    quantity=item["quantity"],
                    unit_price_pkr=menu_by_id[item["menu_item_id"]].price_pkr,
                )
                for item in requested_items
            ]
        )
        RestaurantOrderNotification.objects.bulk_create(
            [
                RestaurantOrderNotification(
                    order=order,
                    channel=channel,
                    available_at=timezone.now(),
                )
                for channel in ("email", "whatsapp")
            ]
        )

    order_logger.info(
        "Order request recorded reference=%s fulfillment=%s item_count=%d",
        order.id,
        data["fulfillment_type"],
        len(requested_items),
    )
    message = (
        "Your delivery order request has been recorded with the selected area's delivery fee. "
        "Please call Saltanat to confirm availability."
        if is_delivery
        else "Your pickup order request has been recorded. Please call Saltanat to confirm it before coming."
    )
    return Response(
        {
            "id": str(order.id),
            "status": "awaiting_confirmation",
            "paymentMethod": "cod",
            "subtotalPkr": subtotal,
            "deliveryArea": delivery_area.name if delivery_area else None,
            "deliveryFeePkr": delivery_area.delivery_fee_pkr if delivery_area else 0,
            "totalPkr": subtotal + delivery_area.delivery_fee_pkr if delivery_area else subtotal,
            "message": message,
        },
        status=status.HTTP_201_CREATED,
    )


def _staff_order_data(order: RestaurantOrder) -> dict:
    return {
        "id": str(order.id),
        "name": order.customer_name,
        "phone": order.phone,
        "fulfillmentType": order.fulfillment_type,
        "deliveryAddress": order.delivery_address,
        "deliveryArea": order.delivery_area,
        "paymentMethod": order.payment_method,
        "orderStatus": order.order_status,
        "paymentStatus": order.payment_status,
        "subtotalPkr": order.subtotal_pkr,
        "deliveryFeePkr": order.delivery_fee_pkr,
        "totalPkr": order.total_pkr,
        "notes": order.notes,
        "createdAt": order.created_at.isoformat(),
        "items": [
            {
                "menuItemId": item.menu_item_id,
                "name": item.item_name,
                "quantity": item.quantity,
                "unitPricePkr": item.unit_price_pkr,
            }
            for item in order.items.all()
        ],
    }


@api_view(["GET"])
@throttle_classes([StaffApiThrottle])
def list_staff_orders(request: HttpRequest):
    _actor, error = staff_actor(request)
    if error:
        return error

    order_status = request.query_params.get("status", "").strip()
    allowed_statuses = {
        "awaiting_confirmation",
        "confirmed",
        "preparing",
        "ready",
        "completed",
        "cancelled",
    }
    if order_status and order_status not in allowed_statuses:
        return Response(
            {"error": "Choose a valid order status filter."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    orders = RestaurantOrder.objects.prefetch_related("items").order_by("-created_at")
    if order_status:
        orders = orders.filter(order_status=order_status)
    return Response([_staff_order_data(order) for order in orders[:100]])


@api_view(["PATCH"])
@throttle_classes([StaffApiThrottle])
def update_staff_order(request: HttpRequest, order_id):
    actor, error = staff_actor(request)
    if error:
        return error

    serializer = StaffOrderUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Please check the order update and try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    changes = serializer.validated_data
    next_status = changes.get("order_status")
    next_payment_status = changes.get("payment_status")
    next_delivery_fee = changes.get("delivery_fee_pkr")

    with transaction.atomic():
        try:
            order = RestaurantOrder.objects.select_for_update().get(id=order_id)
        except RestaurantOrder.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        previous_order_status = order.order_status
        previous_payment_status = order.payment_status
        previous_delivery_fee = order.delivery_fee_pkr
        allowed_transitions = {
            "awaiting_confirmation": {"confirmed", "cancelled"},
            "confirmed": {"preparing", "cancelled"},
            "preparing": {"ready", "cancelled"},
            "ready": {"completed", "cancelled"},
            "completed": set(),
            "cancelled": set(),
        }

        if next_status is not None and next_status not in allowed_transitions.get(
            order.order_status, set()
        ):
            return Response(
                {"error": "That order status transition is not allowed."},
                status=status.HTTP_409_CONFLICT,
            )
        if next_delivery_fee is not None and order.fulfillment_type != "delivery":
            return Response(
                {"error": "A delivery fee can only be set on a delivery order."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            next_status == "confirmed"
            and order.fulfillment_type == "delivery"
            and next_delivery_fee is None
            and order.delivery_fee_pkr is None
        ):
            return Response(
                {"error": "Set the delivery fee before confirming the delivery order."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if next_status == "cancelled" and order.payment_status == "paid":
            return Response(
                {"error": "A paid order cannot be cancelled from this dashboard."},
                status=status.HTTP_409_CONFLICT,
            )
        if next_payment_status == "unpaid" and order.payment_status == "paid":
            return Response(
                {"error": "A collected COD payment cannot be changed back to unpaid."},
                status=status.HTTP_409_CONFLICT,
            )
        effective_status = next_status or order.order_status
        if next_payment_status == "paid" and (
            order.payment_method != "cod" or effective_status != "completed"
        ):
            return Response(
                {"error": "Mark COD as paid only after a COD order is completed."},
                status=status.HTTP_409_CONFLICT,
            )

        if next_status is not None:
            order.order_status = next_status
        if next_payment_status is not None:
            order.payment_status = next_payment_status
        if next_delivery_fee is not None:
            order.delivery_fee_pkr = next_delivery_fee
            order.total_pkr = order.subtotal_pkr + next_delivery_fee

        if (
            order.order_status != previous_order_status
            or order.payment_status != previous_payment_status
            or next_delivery_fee is not None
        ):
            order.save(
                update_fields=[
                    "order_status",
                    "payment_status",
                    "delivery_fee_pkr",
                    "total_pkr",
                ]
            )
            RestaurantOrderAudit.objects.create(
                order=order,
                actor=actor,
                action="staff_update",
                previous_order_status=previous_order_status,
                new_order_status=order.order_status,
                previous_payment_status=previous_payment_status,
                new_payment_status=order.payment_status,
                previous_delivery_fee_pkr=previous_delivery_fee,
                new_delivery_fee_pkr=order.delivery_fee_pkr,
            )

    return Response({"order": _staff_order_data(order)})