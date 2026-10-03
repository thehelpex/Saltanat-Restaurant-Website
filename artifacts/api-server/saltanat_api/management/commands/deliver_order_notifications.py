import logging
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from saltanat_api.models import RestaurantOrderNotification
from saltanat_api.notifications import (
    NotificationDeliveryError,
    NotificationNotConfigured,
    deliver_order_notification,
)


logger = logging.getLogger("saltanat.notifications")


class Command(BaseCommand):
    help = "Deliver pending email and WhatsApp order alerts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Maximum number of pending alerts to claim (1-500).",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if not 1 <= batch_size <= 500:
            raise CommandError("--batch-size must be between 1 and 500.")

        counts = {"sent": 0, "retrying": 0, "not_configured": 0}
        for _ in range(batch_size):
            notification_ids = self._claim_batch(1)
            if not notification_ids:
                break
            notification_id = notification_ids[0]
            notification = RestaurantOrderNotification.objects.select_related(
                "order"
            ).get(pk=notification_id)
            try:
                deliver_order_notification(notification)
            except NotificationNotConfigured as error:
                self._defer_unconfigured(notification, error.channel)
                counts["not_configured"] += 1
            except NotificationDeliveryError as error:
                self._schedule_retry(notification, error.code)
                counts["retrying"] += 1
                logger.error(
                    "Order alert delivery failed reference=%s channel=%s code=%s",
                    notification.order_id,
                    notification.channel,
                    error.code,
                )
            else:
                self._mark_sent(notification)
                counts["sent"] += 1
                logger.info(
                    "Order alert accepted reference=%s channel=%s",
                    notification.order_id,
                    notification.channel,
                )

        self.stdout.write(
            "Order alerts: "
            f"{counts['sent']} sent, {counts['retrying']} scheduled to retry, "
            f"{counts['not_configured']} deferred for missing configuration."
        )
        if counts["not_configured"]:
            raise CommandError(
                "Configure the missing order-alert channel secrets; deferred alerts remain queued."
            )
        if counts["retrying"]:
            raise CommandError(
                "Some order alerts failed and were scheduled for retry; inspect monitored logs."
            )

    @staticmethod
    def _claim_batch(batch_size: int) -> list[int]:
        now = timezone.now()
        stale_claim = Q(status="sending", locked_until__lte=now)
        ready = Q(status="pending", available_at__lte=now)
        with transaction.atomic():
            notifications = list(
                RestaurantOrderNotification.objects.select_for_update(
                    skip_locked=True
                )
                .filter(ready | stale_claim)
                .order_by("created_at")[:batch_size]
            )
            notification_ids = []
            for notification in notifications:
                notification.status = "sending"
                notification.attempt_count += 1
                notification.locked_until = now + timedelta(minutes=10)
                notification.save(
                    update_fields=["status", "attempt_count", "locked_until"]
                )
                notification_ids.append(notification.id)
        return notification_ids

    @staticmethod
    def _defer_unconfigured(
        notification: RestaurantOrderNotification, channel: str
    ) -> None:
        notification.status = "pending"
        notification.attempt_count = max(0, notification.attempt_count - 1)
        notification.available_at = timezone.now() + timedelta(minutes=15)
        notification.locked_until = None
        notification.last_error = f"{channel}_not_configured"
        notification.save(
            update_fields=[
                "status",
                "attempt_count",
                "available_at",
                "locked_until",
                "last_error",
            ]
        )
        logger.error(
            "Order alert deferred reference=%s channel=%s code=not_configured",
            notification.order_id,
            channel,
        )

    @staticmethod
    def _schedule_retry(
        notification: RestaurantOrderNotification, error_code: str
    ) -> None:
        delay_minutes = min(60, 2 ** min(notification.attempt_count - 1, 6))
        notification.status = "pending"
        notification.available_at = timezone.now() + timedelta(
            minutes=delay_minutes
        )
        notification.locked_until = None
        notification.last_error = error_code
        notification.save(
            update_fields=[
                "status",
                "available_at",
                "locked_until",
                "last_error",
            ]
        )

    @staticmethod
    def _mark_sent(notification: RestaurantOrderNotification) -> None:
        notification.status = "sent"
        notification.locked_until = None
        notification.last_error = None
        notification.sent_at = timezone.now()
        notification.save(
            update_fields=["status", "locked_until", "last_error", "sent_at"]
        )
