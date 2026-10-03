import base64
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase, override_settings
from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.db import DatabaseError, connection
from urllib.error import HTTPError
from rest_framework.test import APIClient

from .models import (
    RestaurantDeliveryArea,
    RestaurantMenuCategory,
    RestaurantMenuItem,
    RestaurantOrder,
)
from .management.commands.deliver_order_notifications import Command as DeliverOrderNotifications
from .notifications import (
    NotificationDeliveryError,
    NotificationNotConfigured,
    deliver_order_notification,
    _send_whatsapp,
)
from .payments import PaymentGatewayNotConfigured


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "saltanat-test-throttling",
        }
    },
)
class PublicApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        schema_file = Path(__file__).resolve().parent.parent / "sql" / "create_restaurant_tables.sql"
        with connection.cursor() as cursor:
            for statement in schema_file.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    cursor.execute(statement)
        call_command("import_menu_seed")

    def setUp(self):
        self.client = APIClient()

    @staticmethod
    def manager_headers(password="test-only-password"):
        token = base64.b64encode(
            f"restaurant-staff:{password}".encode("utf-8")
        ).decode("ascii")
        return {"HTTP_AUTHORIZATION": f"Basic {token}"}

    def test_health_check_is_healthy(self):
        response = self.client.get("/api/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})

    @patch("saltanat_api.views.connection.cursor", side_effect=DatabaseError)
    def test_health_check_reports_database_failure(self, _cursor):
        response = self.client.get("/api/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "unavailable", "database": "unavailable"},
        )

    def test_service_root_is_healthy(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})

    @override_settings(CORS_ALLOWED_ORIGINS={"http://127.0.0.1:23336"})
    def test_cors_allows_configured_frontend_origin(self):
        response = self.client.get(
            "/api/healthz",
            HTTP_ORIGIN="http://127.0.0.1:23336",
        )
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "http://127.0.0.1:23336",
        )

    @override_settings(CORS_ALLOWED_ORIGINS={"http://127.0.0.1:23336"})
    def test_cors_preflight_allows_order_submission(self):
        response = self.client.options(
            "/api/restaurant/orders",
            HTTP_ORIGIN="http://127.0.0.1:23336",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "http://127.0.0.1:23336",
        )
        self.assertIn("POST", response["Access-Control-Allow-Methods"])

    def test_menu_filter_matches_category_and_search_case_insensitively(self):
        response = self.client.get(
            "/api/restaurant/menu",
            {"category": "bbq & grills", "search": "BIHARI"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.json()], ["Chicken Bihari Boti", "Beef Bihari Boti"])

    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    @override_settings(DEBUG=True)
    def test_manager_catalog_requires_staff_authentication(self):
        response = self.client.get("/api/manager/menu/categories")
        self.assertEqual(response.status_code, 401)

        wrong_password_response = self.client.get(
            "/api/manager/delivery-areas",
            **self.manager_headers(password="wrong-password"),
        )
        self.assertEqual(wrong_password_response.status_code, 401)

    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    @override_settings(DEBUG=True)
    def test_manager_can_manage_catalog_and_delivery_area(self):
        headers = self.manager_headers()
        category_response = self.client.post(
            "/api/manager/menu/categories",
            {"name": "Test menu category", "sortOrder": 99},
            format="json",
            **headers,
        )
        self.assertEqual(category_response.status_code, 201)
        category_id = category_response.json()["id"]
        category_list = self.client.get(
            "/api/manager/menu/categories", **headers
        )
        self.assertIn(category_id, [row["id"] for row in category_list.json()])
        category_update = self.client.patch(
            f"/api/manager/menu/categories/{category_id}",
            {"name": "Renamed test category", "sortOrder": 5, "isActive": False},
            format="json",
            **headers,
        )
        self.assertEqual(category_update.status_code, 200)
        self.assertEqual(category_update.json()["name"], "Renamed test category")
        self.assertFalse(category_update.json()["isActive"])
        category_reactivate = self.client.patch(
            f"/api/manager/menu/categories/{category_id}",
            {"isActive": True},
            format="json",
            **headers,
        )
        self.assertTrue(category_reactivate.json()["isActive"])
        blank_category_response = self.client.post(
            "/api/manager/menu/categories",
            {"name": "   "},
            format="json",
            **headers,
        )
        self.assertEqual(blank_category_response.status_code, 400)

        item_response = self.client.post(
            "/api/manager/menu/items",
            {
                "name": "Test unavailable dish",
                "categoryId": category_id,
                "pricePkr": 450,
                "isAvailable": False,
            },
            format="json",
            **headers,
        )
        self.assertEqual(item_response.status_code, 201)
        item_id = item_response.json()["id"]
        self.assertFalse(item_response.json()["isAvailable"])
        item_list = self.client.get("/api/manager/menu/items", **headers)
        self.assertIn(item_id, [row["id"] for row in item_list.json()])
        item_update = self.client.patch(
            f"/api/manager/menu/items/{item_id}",
            {"pricePkr": 475, "isAvailable": True, "isActive": False},
            format="json",
            **headers,
        )
        self.assertEqual(item_update.status_code, 200)
        self.assertEqual(item_update.json()["pricePkr"], 475)
        self.assertTrue(item_update.json()["isAvailable"])
        self.assertFalse(item_update.json()["isActive"])
        item_reactivate = self.client.patch(
            f"/api/manager/menu/items/{item_id}",
            {"isActive": True},
            format="json",
            **headers,
        )
        self.assertTrue(item_reactivate.json()["isActive"])
        unsafe_image_response = self.client.post(
            "/api/manager/menu/items",
            {
                "name": "Unsafe image test dish",
                "categoryId": category_id,
                "pricePkr": 100,
                "imageUrl": "//untrusted.example/image.jpg",
            },
            format="json",
            **headers,
        )
        self.assertEqual(unsafe_image_response.status_code, 400)

        area_response = self.client.post(
            "/api/manager/delivery-areas",
            {"name": "Test service zone", "deliveryFeePkr": 275},
            format="json",
            **headers,
        )
        self.assertEqual(area_response.status_code, 201)
        area_id = area_response.json()["id"]
        area_list = self.client.get("/api/manager/delivery-areas", **headers)
        self.assertIn(area_id, [row["id"] for row in area_list.json()])
        area_update = self.client.patch(
            f"/api/manager/delivery-areas/{area_id}",
            {"deliveryFeePkr": 350, "isActive": False},
            format="json",
            **headers,
        )
        self.assertEqual(area_update.status_code, 200)
        self.assertEqual(area_update.json()["deliveryFeePkr"], 350)
        self.assertFalse(area_update.json()["isActive"])
        self.assertNotIn(
            area_id,
            [area["id"] for area in self.client.get("/api/restaurant/delivery-areas").json()],
        )
        area_reactivate = self.client.patch(
            f"/api/manager/delivery-areas/{area_id}",
            {"isActive": True},
            format="json",
            **headers,
        )
        self.assertTrue(area_reactivate.json()["isActive"])
        public_areas = self.client.get("/api/restaurant/delivery-areas")
        self.assertIn(
            area_id,
            [area["id"] for area in public_areas.json()],
        )
        self.assertEqual(
            next(area for area in public_areas.json() if area["id"] == area_id)[
                "deliveryFeePkr"
            ],
            350,
        )
        inactive_area_response = self.client.post(
            "/api/manager/delivery-areas",
            {
                "name": "Inactive test service zone",
                "deliveryFeePkr": 500,
                "isActive": False,
            },
            format="json",
            **headers,
        )
        self.assertEqual(inactive_area_response.status_code, 201)
        inactive_area_id = inactive_area_response.json()["id"]
        self.assertNotIn(
            inactive_area_id,
            [area["id"] for area in self.client.get("/api/restaurant/delivery-areas").json()],
        )

        category_delete = self.client.delete(
            f"/api/manager/menu/categories/{category_id}", **headers
        )
        item_delete = self.client.delete(
            f"/api/manager/menu/items/{item_id}", **headers
        )
        area_delete = self.client.delete(
            f"/api/manager/delivery-areas/{area_id}", **headers
        )
        self.assertEqual(category_delete.status_code, 204)
        self.assertEqual(item_delete.status_code, 204)
        self.assertEqual(area_delete.status_code, 204)

        category_list_after_delete = self.client.get(
            "/api/manager/menu/categories", **headers
        )
        item_list_after_delete = self.client.get("/api/manager/menu/items", **headers)
        area_list_after_delete = self.client.get(
            "/api/manager/delivery-areas", **headers
        )
        self.assertFalse(
            next(row for row in category_list_after_delete.json() if row["id"] == category_id)[
                "isActive"
            ]
        )
        self.assertFalse(
            next(row for row in item_list_after_delete.json() if row["id"] == item_id)[
                "isActive"
            ]
        )
        self.assertFalse(
            next(row for row in area_list_after_delete.json() if row["id"] == area_id)[
                "isActive"
            ]
        )
        self.assertNotIn(
            area_id,
            [area["id"] for area in self.client.get("/api/restaurant/delivery-areas").json()],
        )

    def test_public_menu_hides_inactive_items_and_rejects_unavailable_items(self):
        active_category = RestaurantMenuCategory.objects.create(
            name="Orderability test category",
            sort_order=999,
            is_active=True,
        )
        hidden_category = RestaurantMenuCategory.objects.create(
            name="Inactive orderability category",
            sort_order=1000,
            is_active=False,
        )
        unavailable_item = RestaurantMenuItem.objects.create(
            category=active_category,
            name="Unavailable orderability item",
            price_pkr=550,
            is_active=True,
            is_available=False,
        )
        hidden_item = RestaurantMenuItem.objects.create(
            category=active_category,
            name="Inactive orderability item",
            price_pkr=650,
            is_active=False,
            is_available=True,
        )
        inactive_category_item = RestaurantMenuItem.objects.create(
            category=hidden_category,
            name="Inactive category orderability item",
            price_pkr=650,
            is_active=True,
            is_available=True,
        )

        public_items = self.client.get("/api/restaurant/menu").json()
        by_name = {item["name"]: item for item in public_items}
        self.assertIn(unavailable_item.name, by_name)
        self.assertFalse(by_name[unavailable_item.name]["isAvailable"])
        self.assertNotIn(hidden_item.name, by_name)
        self.assertNotIn(inactive_category_item.name, by_name)

        with patch("saltanat_api.views.RestaurantOrder.objects.create") as create_order:
            for item in (unavailable_item, hidden_item, inactive_category_item):
                response = self.client.post(
                    "/api/restaurant/orders",
                    {
                        "name": "Amina Khan",
                        "phone": "021 111 2222",
                        "fulfillmentType": "pickup",
                        "paymentMethod": "cod",
                        "items": [{"menuItemId": item.id, "quantity": 1}],
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
            create_order.assert_not_called()

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

    @patch("saltanat_api.views.RestaurantOrderNotification.objects.bulk_create")
    @patch("saltanat_api.views.RestaurantOrderItem.objects.bulk_create")
    @patch("saltanat_api.views.RestaurantOrder.objects.create")
    def test_pickup_order_uses_server_menu_prices(
        self, create_order, create_items, create_notifications
    ):
        order_id = uuid.uuid4()
        create_order.return_value = RestaurantOrder(id=order_id)
        response = self.client.post(
            "/api/restaurant/orders",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "fulfillmentType": "pickup",
                "paymentMethod": "cod",
                "items": [{"menuItemId": 1, "quantity": 2, "pricePkr": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["subtotalPkr"], 1998)
        self.assertEqual(response.json()["totalPkr"], 1998)
        self.assertEqual(create_order.call_args.kwargs["subtotal_pkr"], 1998)
        self.assertEqual(create_order.call_args.kwargs["payment_status"], "unpaid")
        self.assertEqual(create_items.call_args.args[0][0].unit_price_pkr, 999)
        self.assertEqual(
            [row.channel for row in create_notifications.call_args.args[0]],
            ["email", "whatsapp"],
        )

    @patch("saltanat_api.throttling.OrderCreationThrottle.rate", "1/minute", create=True)
    @patch("saltanat_api.views.RestaurantOrderNotification.objects.bulk_create")
    @patch("saltanat_api.views.RestaurantOrderItem.objects.bulk_create")
    @patch("saltanat_api.views.RestaurantOrder.objects.create")
    def test_order_submission_is_rate_limited(
        self, create_order, _create_items, _create_notifications
    ):
        cache.clear()
        create_order.return_value = RestaurantOrder(id=uuid.uuid4())
        payload = {
            "name": "Amina Khan",
            "phone": "021 111 2222",
            "fulfillmentType": "pickup",
            "paymentMethod": "cod",
            "items": [{"menuItemId": 1, "quantity": 1}],
        }
        first_response = self.client.post(
            "/api/restaurant/orders", payload, format="json"
        )
        second_response = self.client.post(
            "/api/restaurant/orders", payload, format="json"
        )
        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 429)
        create_order.assert_called_once()

    @patch("saltanat_api.views.RestaurantOrderNotification.objects.bulk_create")
    @patch("saltanat_api.views.RestaurantOrderItem.objects.bulk_create")
    @patch("saltanat_api.views.RestaurantOrder.objects.create")
    def test_delivery_order_uses_active_area_fee_and_calculates_total(
        self, create_order, _create_items, _create_notifications
    ):
        order_id = uuid.uuid4()
        create_order.return_value = RestaurantOrder(id=order_id)
        area = RestaurantDeliveryArea.objects.create(
            name="Gulshan order test",
            delivery_fee_pkr=500,
            is_active=True,
        )
        response = self.client.post(
            "/api/restaurant/orders",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "fulfillmentType": "delivery",
                "deliveryAddress": "Plot 118, Stadium Road",
                "deliveryAreaId": area.id,
                "paymentMethod": "cod",
                "items": [{"menuItemId": 1, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["deliveryArea"], area.name)
        self.assertEqual(response.json()["deliveryFeePkr"], 500)
        self.assertEqual(response.json()["totalPkr"], 1499)
        self.assertEqual(create_order.call_args.kwargs["delivery_fee_pkr"], 500)
        self.assertEqual(create_order.call_args.kwargs["total_pkr"], 1499)
        self.assertEqual(create_order.call_args.kwargs["delivery_area"], area.name)
        self.assertEqual(create_order.call_args.kwargs["delivery_area_ref"], area)

    @patch("saltanat_api.views.RestaurantOrder.objects.create")
    def test_delivery_order_rejects_missing_or_inactive_area(self, create_order):
        inactive_area = RestaurantDeliveryArea.objects.create(
            name="Inactive order test area",
            delivery_fee_pkr=500,
            is_active=False,
        )
        for delivery_area_id in (None, inactive_area.id):
            payload = {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "fulfillmentType": "delivery",
                "deliveryAddress": "Plot 118, Stadium Road",
                "paymentMethod": "cod",
                "items": [{"menuItemId": 1, "quantity": 1}],
            }
            if delivery_area_id is not None:
                payload["deliveryAreaId"] = delivery_area_id
            response = self.client.post(
                "/api/restaurant/orders",
                payload,
                format="json",
            )
            self.assertEqual(response.status_code, 400)
        create_order.assert_not_called()

    def test_delivery_order_requires_an_address(self):
        response = self.client.post(
            "/api/restaurant/orders",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "fulfillmentType": "delivery",
                "paymentMethod": "cod",
                "items": [{"menuItemId": 1, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("saltanat_api.views.RestaurantOrder.objects.create")
    def test_order_rejects_menu_items_not_in_current_menu(self, create_order):
        response = self.client.post(
            "/api/restaurant/orders",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "fulfillmentType": "pickup",
                "paymentMethod": "cod",
                "items": [{"menuItemId": 999, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        create_order.assert_not_called()

    @patch("saltanat_api.views.get_hosted_payment_gateway", side_effect=PaymentGatewayNotConfigured)
    @patch("saltanat_api.views.RestaurantOrder.objects.create")
    def test_card_order_is_not_stored_until_a_gateway_is_configured(
        self, create_order, _get_gateway
    ):
        response = self.client.post(
            "/api/restaurant/orders",
            {
                "name": "Amina Khan",
                "phone": "021 111 2222",
                "fulfillmentType": "pickup",
                "paymentMethod": "card",
                "items": [{"menuItemId": 1, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 503)
        create_order.assert_not_called()

    @patch.dict(
        os.environ,
        {
            "ORDER_ALERT_SMTP_HOST": "smtp.example.test",
            "ORDER_ALERT_SMTP_USERNAME": "alerts",
            "ORDER_ALERT_SMTP_PASSWORD": "test-secret",
            "ORDER_ALERT_FROM_EMAIL": "orders@example.test",
            "ORDER_ALERT_EMAIL_RECIPIENTS": "staff@example.test",
        },
        clear=True,
    )
    @patch("saltanat_api.notifications.get_connection")
    def test_email_alert_uses_configured_smtp_without_customer_data(
        self, get_connection
    ):
        connection = MagicMock()
        connection.send_messages.return_value = 1
        get_connection.return_value = connection
        order = SimpleNamespace(
            id=uuid.uuid4(),
            fulfillment_type="pickup",
            subtotal_pkr=999,
            total_pkr=999,
        )
        notification = SimpleNamespace(channel="email", order=order)
        deliver_order_notification(notification)
        get_connection.assert_called_once_with(
            "django.core.mail.backends.smtp.EmailBackend",
            host="smtp.example.test",
            port=587,
            username="alerts",
            password="test-secret",
            use_tls=True,
            timeout=10,
        )
        message = connection.send_messages.call_args.args[0][0]
        self.assertNotIn("customer", message.body.casefold())
        self.assertIn("staff dashboard", message.body)

    @patch.dict(
        os.environ,
        {
            "WHATSAPP_ACCESS_TOKEN": "test-token",
            "WHATSAPP_PHONE_NUMBER_ID": "123456789",
            "WHATSAPP_ORDER_TEMPLATE_NAME": "new_order",
            "WHATSAPP_GRAPH_API_VERSION": "v99.0",
            "WHATSAPP_ALERT_RECIPIENTS": "923001234567",
        },
        clear=True,
    )
    @patch("saltanat_api.notifications.urlopen")
    def test_whatsapp_alert_uses_template_and_omits_customer_details(self, urlopen):
        urlopen.return_value.__enter__.return_value.status = 200
        order = SimpleNamespace(
            id=uuid.uuid4(),
            fulfillment_type="delivery",
            subtotal_pkr=1998,
        )
        notification = SimpleNamespace(
            channel="whatsapp",
            order=order,
            delivered_recipients=[],
            save=Mock(),
        )
        deliver_order_notification(
            notification
        )
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["messaging_product"], "whatsapp")
        self.assertEqual(payload["template"]["name"], "new_order")
        self.assertEqual(payload["to"], "923001234567")
        self.assertEqual(
            [item["text"] for item in payload["template"]["components"][0]["parameters"]],
            [str(order.id)[:8], "delivery", "PKR 1998"],
        )
        self.assertEqual(
            urlopen.call_args.args[0].full_url,
            f"https://graph.facebook.com/v99.0/123456789/messages",
        )

    @patch.dict(
        os.environ,
        {
            "WHATSAPP_ACCESS_TOKEN": "test-token",
            "WHATSAPP_PHONE_NUMBER_ID": "123456789",
            "WHATSAPP_ORDER_TEMPLATE_NAME": "new_order",
            "WHATSAPP_GRAPH_API_VERSION": "v99.0",
            "WHATSAPP_ALERT_RECIPIENTS": "923001234567,923009876543",
        },
        clear=True,
    )
    @patch("saltanat_api.notifications.urlopen")
    def test_whatsapp_retry_skips_recipients_already_sent(self, urlopen):
        first_response = MagicMock()
        first_response.__enter__.return_value.status = 200
        urlopen.side_effect = [
            first_response,
            HTTPError("https://graph.facebook.com/test", 503, "Unavailable", {}, None),
        ]
        notification = SimpleNamespace(
            order=SimpleNamespace(
                id=uuid.uuid4(),
                fulfillment_type="pickup",
                subtotal_pkr=999,
            ),
            delivered_recipients=[],
            save=Mock(),
        )

        with self.assertRaises(NotificationDeliveryError):
            _send_whatsapp(notification)
        self.assertEqual(notification.delivered_recipients, ["923001234567"])

        retry_response = MagicMock()
        retry_response.__enter__.return_value.status = 200
        urlopen.side_effect = [retry_response]
        _send_whatsapp(notification)

        self.assertEqual(len(urlopen.call_args_list), 3)
        self.assertEqual(
            json.loads(urlopen.call_args_list[2].args[0].data)["to"],
            "923009876543",
        )
        self.assertEqual(
            notification.delivered_recipients,
            ["923001234567", "923009876543"],
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_order_alert_reports_missing_email_configuration(self):
        with self.assertRaises(NotificationNotConfigured) as error:
            deliver_order_notification(
                SimpleNamespace(channel="email", order=SimpleNamespace())
            )
        self.assertEqual(error.exception.channel, "email")

    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.Command._claim_batch",
        side_effect=[[42], []],
    )
    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.RestaurantOrderNotification.objects.select_related"
    )
    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.deliver_order_notification"
    )
    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.Command._mark_sent"
    )
    def test_notification_worker_marks_provider_acceptance_as_sent(
        self, mark_sent, deliver, select_related, _claim_batch
    ):
        notification = SimpleNamespace(id=42, order_id=uuid.uuid4(), channel="email")
        select_related.return_value.get.return_value = notification
        call_command("deliver_order_notifications")
        deliver.assert_called_once_with(notification)
        mark_sent.assert_called_once_with(notification)

    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.Command._claim_batch",
        side_effect=[[42], []],
    )
    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.RestaurantOrderNotification.objects.select_related"
    )
    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.deliver_order_notification",
        side_effect=NotificationDeliveryError("email_transport_error"),
    )
    @patch(
        "saltanat_api.management.commands.deliver_order_notifications.Command._schedule_retry"
    )
    def test_notification_worker_schedules_transient_failure_for_retry(
        self, schedule_retry, _deliver, select_related, _claim_batch
    ):
        notification = SimpleNamespace(id=42, order_id=uuid.uuid4(), channel="email")
        select_related.return_value.get.return_value = notification
        with self.assertRaises(CommandError):
            call_command("deliver_order_notifications")
        schedule_retry.assert_called_once_with(
            notification, "email_transport_error"
        )

    def test_notification_retry_uses_backoff_and_saves_safe_error_code(self):
        notification = SimpleNamespace(
            attempt_count=4,
            save=Mock(),
        )
        DeliverOrderNotifications._schedule_retry(
            notification, "whatsapp_transport_error"
        )
        self.assertEqual(notification.status, "pending")
        self.assertEqual(notification.last_error, "whatsapp_transport_error")
        self.assertIsNone(notification.locked_until)
        self.assertGreater(notification.available_at, datetime.now(timezone.utc))
        notification.save.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    def test_staff_orders_require_valid_credentials(self):
        response = self.client.get("/api/staff/orders", secure=True)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response["WWW-Authenticate"])

        token = base64.b64encode(b"restaurant-staff:wrong-password").decode()
        response = self.client.get(
            "/api/staff/orders",
            secure=True,
            HTTP_AUTHORIZATION=f"Basic {token}",
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    def test_staff_api_rejects_insecure_production_requests(self):
        response = self.client.get("/api/staff/orders")
        self.assertEqual(response.status_code, 400)
        self.assertIn("HTTPS", response.json()["error"])

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True)
    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    def test_production_http_staff_request_redirects_to_https(self):
        response = self.client.get("/api/staff/orders")
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("https://"))

    @override_settings(DEBUG=True)
    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    def test_staff_api_allows_http_only_in_debug_mode(self):
        response = self.client.get("/api/staff/orders")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response["WWW-Authenticate"])

    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    @patch("saltanat_api.views.RestaurantOrder.objects.prefetch_related")
    def test_staff_can_list_orders_with_basic_auth(self, prefetch_related):
        queryset = MagicMock()
        queryset.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.__getitem__.return_value = []
        prefetch_related.return_value = queryset
        token = base64.b64encode(b"restaurant-staff:test-only-password").decode()
        response = self.client.get(
            "/api/staff/orders?status=awaiting_confirmation",
            secure=True,
            HTTP_AUTHORIZATION=f"Basic {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        queryset.filter.assert_called_once_with(order_status="awaiting_confirmation")

    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    @patch("saltanat_api.views.RestaurantOrderAudit.objects.create")
    @patch("saltanat_api.views.RestaurantOrder.objects.select_for_update")
    def test_staff_can_confirm_pickup_and_action_is_audited(
        self, select_for_update, create_audit
    ):
        order = SimpleNamespace(
            id=uuid.uuid4(),
            customer_name="Amina Khan",
            phone="021 111 2222",
            fulfillment_type="pickup",
            delivery_address=None,
            delivery_area=None,
            payment_method="cod",
            order_status="awaiting_confirmation",
            payment_status="unpaid",
            subtotal_pkr=999,
            delivery_fee_pkr=0,
            total_pkr=999,
            notes=None,
            created_at=datetime.now(timezone.utc),
            items=SimpleNamespace(all=lambda: []),
            save=Mock(),
        )
        select_for_update.return_value.get.return_value = order
        token = base64.b64encode(b"restaurant-staff:test-only-password").decode()
        response = self.client.patch(
            f"/api/staff/orders/{order.id}",
            {"orderStatus": "confirmed"},
            format="json",
            secure=True,
            HTTP_AUTHORIZATION=f"Basic {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["order"]["orderStatus"], "confirmed")
        create_audit.assert_called_once()
        self.assertEqual(create_audit.call_args.kwargs["actor"], "restaurant-staff")

    @patch.dict(
        os.environ,
        {
            "STAFF_DASHBOARD_USERNAME": "restaurant-staff",
            "STAFF_DASHBOARD_PASSWORD": "test-only-password",
        },
    )
    @patch("saltanat_api.views.RestaurantOrder.objects.select_for_update")
    def test_delivery_order_cannot_be_confirmed_without_fee(self, select_for_update):
        order = SimpleNamespace(
            id=uuid.uuid4(),
            fulfillment_type="delivery",
            order_status="awaiting_confirmation",
            payment_status="unpaid",
            delivery_fee_pkr=None,
        )
        select_for_update.return_value.get.return_value = order
        token = base64.b64encode(b"restaurant-staff:test-only-password").decode()
        response = self.client.patch(
            f"/api/staff/orders/{order.id}",
            {"orderStatus": "confirmed"},
            format="json",
            secure=True,
            HTTP_AUTHORIZATION=f"Basic {token}",
        )
        self.assertEqual(response.status_code, 400)