from typing import Protocol

from django.conf import settings
from django.utils.module_loading import import_string


class PaymentGatewayNotConfigured(Exception):
    pass


class HostedPaymentGateway(Protocol):
    def create_checkout_session(self, *, order_reference: str, amount_pkr: int) -> str: ...


def get_hosted_payment_gateway() -> HostedPaymentGateway:
    gateway_path = getattr(settings, "PAYMENT_GATEWAY_CLASS", None)
    if not gateway_path:
        raise PaymentGatewayNotConfigured
    return import_string(gateway_path)()
