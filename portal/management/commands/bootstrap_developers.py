"""Create initial developer accounts from a temporary Railway environment variable.

Set BOOTSTRAP_DEVELOPERS_JSON to a JSON array of {username, password}.
Existing accounts are never overwritten. Clear this variable after verification.
"""
import json
import os
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.models import Profile


class Command(BaseCommand):
    help = "Create development-team accounts once from BOOTSTRAP_DEVELOPERS_JSON"

    def handle(self, *args, **options):
        raw = os.getenv("BOOTSTRAP_DEVELOPERS_JSON", "").strip()
        if not raw:
            self.stdout.write("Developer bootstrap not configured, skipping.")
            return

        try:
            accounts = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise CommandError("BOOTSTRAP_DEVELOPERS_JSON must contain valid JSON") from exc
        if not isinstance(accounts, list) or not 1 <= len(accounts) <= 10:
            raise CommandError("Developer bootstrap requires 1-10 accounts")

        seen = set()
        validated = []
        for entry in accounts:
            if not isinstance(entry, dict):
                raise CommandError("Each developer must have a username and password")
            username = entry.get("username")
            password = entry.get("password")
            if not isinstance(username, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,39}", username):
                raise CommandError("Developer usernames must be lowercase alphanumeric or hyphen (3-40 chars)")
            if not isinstance(password, str) or len(password) < 16:
                raise CommandError("Developer passwords must be at least 16 characters long")
            if username in seen:
                raise CommandError("Duplicate developer username")
            seen.add(username)
            validated.append((username, password))

        User = get_user_model()
        with transaction.atomic():
            for username, password in validated:
                if User.objects.filter(username=username).exists():
                    self.stdout.write(f"Developer account {username} already exists, skipped.")
                    continue
                user = User.objects.create_user(
                    username=username, password=password, is_active=True,
                    is_staff=False, is_superuser=False
                )
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.role = Profile.Role.DEVELOPER
                profile.save(update_fields=["role"])
                self.stdout.write(self.style.SUCCESS(f"Developer account {username} created."))
        self.stdout.write("Remove BOOTSTRAP_DEVELOPERS_JSON from Railway after verification.")
