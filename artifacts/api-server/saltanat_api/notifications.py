import json
import os
import re
import smtplib
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.mail import EmailMessage, get_connection

from .models import RestaurantOrderNotification


class NotificationNotConfigured(Exception):
    def __init__(self, channel: str):
        super().__init__(channel)
        self.channel = channel


class NotificationDeliveryError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def deliver_order_notification(notification: RestaurantOrderNotification) -> None:
    if notification.channel == "email":
        _send_email(notification)
    elif notification.channel == "whatsapp":
        _send_whatsapp(notification)
    else:
        raise ValueError(f"Unsupported order notification channel: {notification.channel}")


def _send_email(notification: RestaurantOrderNotification) -> None:
    config = {
        "host": os.environ.get("ORDER_ALERT_SMTP_HOST"),
        "username": os.environ.get("ORDER_ALERT_SMTP_USERNAME"),
        "password": os.environ.get("ORDER_ALERT_SMTP_PASSWORD"),
        "from_email": os.environ.get("ORDER_ALERT_FROM_EMAIL"),
    }
    recipients = _env_list("ORDER_ALERT_EMAIL_RECIPIENTS")
    if not all(config.values()) or not recipients:
        raise NotificationNotConfigured("email")

    try:
        port = int(os.environ.get("ORDER_ALERT_SMTP_PORT", "587"))
    except ValueError as error:
        raise NotificationNotConfigured("email") from error
    if not 1 <= port <= 65535:
        raise NotificationNotConfigured("email")

    order = notification.order
    fulfillment = order.fulfillment_type
    total = (
        f"PKR {order.total_pkr}"
        if order.total_pkr is not None
        else "To be confirmed by staff"
    )
    body = "\n".join(
        [
            f"New order request: {order.id}",
            f"Fulfillment: {fulfillment}",
            f"Food subtotal: PKR {order.subtotal_pkr}",
            f"Current total: {total}",
            "Review the request in the staff dashboard before confirming.",
        ]
    )
    connection = get_connection(
        "django.core.mail.backends.smtp.EmailBackend",
        host=config["host"],
        port=port,
        username=config["username"],
        password=config["password"],
        use_tls=True,
        timeout=10,
    )
    message = EmailMessage(
        subject=f"New Saltanat order {str(order.id)[:8]}",
        body=body,
        from_email=config["from_email"],
        to=recipients,
        connection=connection,
    )
    try:
        sent_count = message.send(fail_silently=False)
    except (OSError, smtplib.SMTPException) as error:
        raise NotificationDeliveryError("email_transport_error") from error
    if sent_count != 1:
        raise NotificationDeliveryError("email_not_accepted")


def _send_whatsapp(notification: RestaurantOrderNotification) -> None:
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    template_name = os.environ.get("WHATSAPP_ORDER_TEMPLATE_NAME")
    language = os.environ.get("WHATSAPP_TEMPLATE_LANGUAGE", "en")
    api_version = os.environ.get("WHATSAPP_GRAPH_API_VERSION", "")
    recipients = _env_list("WHATSAPP_ALERT_RECIPIENTS")
    if (
        not access_token
        or not phone_number_id
        or not template_name
        or not recipients
        or len(recipients) > 20
        or not re.fullmatch(r"v\d+\.\d+", api_version)
        or any(not re.fullmatch(r"\+?\d{8,15}", recipient) for recipient in recipients)
    ):
        raise NotificationNotConfigured("whatsapp")
    recipients = [recipient.lstrip("+") for recipient in recipients]

    order = notification.order
    payload = {
        "messaging_product": "whatsapp",
        "to": "",
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(order.id)[:8]},
                        {"type": "text", "text": order.fulfillment_type},
                        {"type": "text", "text": f"PKR {order.subtotal_pkr}"},
                    ],
                }
            ],
        },
    }
    endpoint = (
        f"https://graph.facebook.com/{api_version}/"
        f"{phone_number_id}/messages"
    )
    for recipient in recipients:
        if recipient in notification.delivered_recipients:
            continue
        payload["to"] = recipient
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                if response.status < 200 or response.status >= 300:
                    raise NotificationDeliveryError(
                        f"whatsapp_http_{response.status}"
                    )
        except HTTPError as error:
            raise NotificationDeliveryError(
                f"whatsapp_http_{error.code}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise NotificationDeliveryError(
                "whatsapp_transport_error"
            ) from error
        notification.delivered_recipients.append(recipient)
        notification.save(update_fields=["delivered_recipients"])


def _env_list(name: str) -> list[str]:
    return [
        value.strip()
        for value in os.environ.get(name, "").split(",")
        if value.strip()
    ]
