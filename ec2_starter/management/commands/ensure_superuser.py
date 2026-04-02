import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Idempotent superuser creation. Safe to run on every deploy.

    Reads credentials from environment variables so secrets never
    appear in shell history or process listings.

    Usage:
        python manage.py ensure_superuser

    Required environment variables:
        DJANGO_SUPERUSER_USERNAME
        DJANGO_SUPERUSER_EMAIL
        DJANGO_SUPERUSER_PASSWORD
    """

    help = "Create a superuser if one does not already exist (idempotent)"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        # Fail loudly — a missing secret on first deploy should stop the
        # bootstrap, not silently leave the site without an admin account.
        if not username:
            raise CommandError(
                "DJANGO_SUPERUSER_USERNAME environment variable is not set."
            )
        if not password:
            raise CommandError(
                "DJANGO_SUPERUSER_PASSWORD environment variable is not set."
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser '{username}' already exists — skipping creation."
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Superuser '{username}' created successfully.")
        )
