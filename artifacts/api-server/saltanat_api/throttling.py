from rest_framework.throttling import AnonRateThrottle


class OrderCreationThrottle(AnonRateThrottle):
    scope = "order_create"


class ReservationCreationThrottle(AnonRateThrottle):
    scope = "reservation_create"


class EventInquiryCreationThrottle(AnonRateThrottle):
    scope = "event_inquiry_create"


class StaffApiThrottle(AnonRateThrottle):
    scope = "staff_api"
