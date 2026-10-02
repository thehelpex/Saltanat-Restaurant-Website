import uuid
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient


class PublicApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_is_healthy(self):
        response = self.client.get("/api/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_service_root_is_healthy(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_menu_filter_matches_category_and_search_case_insensitively(self):
        response = self.client.get(
            "/api/restaurant/menu",
            {"category": "bbq & grills", "search": "BIHARI"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.json()], ["Chicken Bihari Boti", "Beef Bihari Boti"])

    def test_invalid_reservation_returns_contract_error(self):
        response = self.client.post(
            "/api/restaurant/reservations",
            {"name": "A", "phone": "123", "preferredDate": "not-a-date"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Please check the reservation details and try again."},
        )

    @patch("saltanat_api.views.ReservationRequest.objects.create")
    def test_reservation_is_saved_as_awaiting_confirmation(self, create_reservation):
        reservation_id = uuid.uuid4()
        create_reservation.return_value = SimpleNamespace(id=reservation_id)
        response = self.client.post(
            "/api/restaurant/reservations",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "preferredDate": "2030-03-15",
                "preferredTime": "19:30",
                "guestCount": 4,
                "notes": None,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], str(reservation_id))
        self.assertEqual(response.json()["status"], "awaiting_confirmation")
        self.assertEqual(create_reservation.call_args.kwargs["status"], "awaiting_confirmation")

    @patch("saltanat_api.views.EventInquiry.objects.create")
    def test_event_inquiry_is_saved_with_received_status(self, create_inquiry):
        inquiry_id = uuid.uuid4()
        create_inquiry.return_value = SimpleNamespace(id=inquiry_id)
        response = self.client.post(
            "/api/restaurant/event-inquiries",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "email": None,
                "eventType": "family-gathering",
                "preferredDate": None,
                "guestCount": 20,
                "notes": None,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], str(inquiry_id))
        self.assertEqual(response.json()["status"], "received")
        self.assertEqual(create_inquiry.call_args.kwargs["status"], "received")