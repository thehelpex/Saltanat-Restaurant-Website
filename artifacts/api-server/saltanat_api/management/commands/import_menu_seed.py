import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from saltanat_api.models import RestaurantMenuCategory, RestaurantMenuItem


class Command(BaseCommand):
    help = "Import curated menu_data.json into the manager-editable menu tables."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Overwrite existing category and product fields from the seed file.",
        )

    def handle(self, *args, **options):
        seed_file = Path(__file__).resolve().parents[3] / "menu_data.json"
        try:
            menu_items = json.loads(seed_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(f"Could not read curated menu seed: {error}") from error
        if not isinstance(menu_items, list) or not menu_items:
            raise CommandError("The menu seed must contain at least one item.")
        if connection.vendor != "postgresql":
            raise CommandError("Menu seed import is supported only for PostgreSQL.")

        category_ids = {}
        for sort_order, name in enumerate(dict.fromkeys(item["category"] for item in menu_items)):
            category, created = RestaurantMenuCategory.objects.get_or_create(
                name=name,
                defaults={"sort_order": sort_order, "is_active": True},
            )
            if options["update_existing"] and not created:
                category.sort_order = sort_order
                category.is_active = True
                category.save(update_fields=["sort_order", "is_active"])
            category_ids[name] = category.id

        imported = 0
        updated = 0
        for sort_order, item_data in enumerate(menu_items):
            values = {
                "category_id": category_ids[item_data["category"]],
                "name": item_data["name"],
                "description": item_data.get("description"),
                "price_pkr": item_data["pricePkr"],
                "image_url": item_data.get("imageUrl"),
                "is_featured": item_data.get("isFeatured", False),
                "is_available": True,
                "is_active": True,
                "sort_order": sort_order,
            }
            item, created = RestaurantMenuItem.objects.get_or_create(
                id=item_data["id"],
                defaults=values,
            )
            if created:
                imported += 1
            elif options["update_existing"]:
                RestaurantMenuItem.objects.filter(id=item.id).update(**values)
                updated += 1

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('restaurant_menu_items', 'id'),
                    COALESCE((SELECT MAX(id) FROM restaurant_menu_items), 1),
                    EXISTS(SELECT 1 FROM restaurant_menu_items)
                )
                """
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Menu import complete: {imported} added, {updated} updated. "
                "Existing manager edits were preserved unless --update-existing was used."
            )
        )
