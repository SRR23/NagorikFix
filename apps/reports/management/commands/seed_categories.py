"""Seed default one-click report categories."""
from django.core.management.base import BaseCommand

from apps.reports.models import Category
from utils.constants import DEFAULT_CATEGORIES


class Command(BaseCommand):
    help = "Create default infrastructure report categories if missing."

    def handle(self, *args, **options):
        created_count = 0
        for item in DEFAULT_CATEGORIES:
            _, created = Category.objects.get_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "sort_order": item["sort_order"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {item['name']}"))
            else:
                self.stdout.write(f"Exists: {item['name']}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {created_count} new categor(ies).")
        )
