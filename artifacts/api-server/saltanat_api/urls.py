from django.urls import path

from . import views


urlpatterns = [
    path("", views.health_check, name="root-health"),
    path("api/healthz", views.health_check, name="health-check"),
    path("api/restaurant/menu", views.list_restaurant_menu, name="restaurant-menu"),
    path(
        "api/restaurant/delivery-areas",
        views.list_delivery_areas,
        name="delivery-areas",
    ),
    path("api/restaurant/orders", views.create_restaurant_order, name="restaurant-order"),
    path("api/staff/orders", views.list_staff_orders, name="staff-orders"),
    path(
        "api/staff/orders/<uuid:order_id>",
        views.update_staff_order,
        name="staff-order-update",
    ),
    path("api/manager/menu/categories", views.manager_categories, name="manager-categories"),
    path(
        "api/manager/menu/categories/<int:category_id>",
        views.manager_category_detail,
        name="manager-category-detail",
    ),
    path("api/manager/menu/items", views.manager_menu_items, name="manager-menu-items"),
    path(
        "api/manager/menu/items/<int:item_id>",
        views.manager_menu_item_detail,
        name="manager-menu-item-detail",
    ),
    path(
        "api/manager/delivery-areas",
        views.manager_delivery_areas,
        name="manager-delivery-areas",
    ),
    path(
        "api/manager/delivery-areas/<int:area_id>",
        views.manager_delivery_area_detail,
        name="manager-delivery-area-detail",
    ),
    path(
        "api/manager/reservations",
        views.manager_reservations,
        name="manager-reservations",
    ),
    path(
        "api/manager/reservations/<uuid:reservation_id>",
        views.manager_reservation_detail,
        name="manager-reservation-detail",
    ),
    path(
        "api/manager/event-inquiries",
        views.manager_event_inquiries,
        name="manager-event-inquiries",
    ),
    path(
        "api/manager/event-inquiries/<uuid:inquiry_id>",
        views.manager_event_inquiry_detail,
        name="manager-event-inquiry-detail",
    ),
    path(
        "api/manager/orders",
        views.list_staff_orders,
        name="manager-orders",
    ),
    path(
        "api/restaurant/reservations",
        views.create_reservation_request,
        name="reservation-request",
    ),
    path(
        "api/restaurant/event-inquiries",
        views.create_event_inquiry,
        name="event-inquiry",
    ),
]