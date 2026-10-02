from django.urls import path

from . import views


urlpatterns = [
    path("", views.health_check, name="root-health"),
    path("api/healthz", views.health_check, name="health-check"),
    path("api/restaurant/menu", views.list_restaurant_menu, name="restaurant-menu"),
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