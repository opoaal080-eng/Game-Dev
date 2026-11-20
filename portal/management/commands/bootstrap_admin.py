"""Optionally create the first administrator from Railway environment variables.

Credentials are used only when no user with this username exists.
Remove the BOOTSTRAP_ADMIN_* variables after first successful deployment.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create an initial superuser once, from BOOTSTRAP_ADMIN_* variables"

    def handle(self, *args, **options):
        username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "").strip()
        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
        email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip()

        if not username and not password:
            self.stdout.write("Admin bootstrap not configured, skipping.")
            return

        if not username or len(password) < 16:
            raise CommandError("Set BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD (16+ characters).")

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write("Administrator already exists, bootstrap skipped.")
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS("Initial administrator created. Remove bootstrap variables now."))
