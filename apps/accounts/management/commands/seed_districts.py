"""Seed Bangladesh districts."""
from django.core.management.base import BaseCommand

from apps.accounts.districts_data import DISTRICTS
from apps.accounts.models import District


class Command(BaseCommand):
    help = "Create Bangladesh district rows if missing."

    def handle(self, *args, **options):
        created_count = 0
        for name, name_bn, code in DISTRICTS:
            _, created = District.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "name_bn": name_bn,
                    "is_active": True,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_count} new district(s). "
                f"Total: {District.objects.count()}."
            )
        )
