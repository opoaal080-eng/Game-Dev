"""Replace the active Nightwell Dev developer roster from a one-time Railway secret.

Do not commit passwords to the repository. Set NIGHTWELL_REPLACE_DEVELOPERS_JSON
temporarily, deploy once, then clear it. Existing posts and task ownership stay
intact: former developers are disabled instead of physically deleted.
"""
import json
import os
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.models import AppSession, Profile


class Command(BaseCommand):
    help = "Replace active developers exactly once using a temporary JSON secret"

    def handle(self, *args, **kwargs):
        raw = os.getenv("NIGHTWELL_REPLACE_DEVELOPERS_JSON", "").strip()
        if not raw:
            return

        try:
            requested = json.loads(raw)
        except ValueError as exc:
            raise CommandError("Malformed developer roster JSON") from exc
        if not isinstance(requested, list) or len(requested) != 3:
            raise CommandError("Exactly three developer accounts must be provided")

        cleaned = []
        seen = set()
        for record in requested:
            if not isinstance(record, dict):
                raise CommandError("Invalid developer record")
            username = record.get("username")
            password = record.get("password")
            job_title = record.get("job_title")
            # The exact requested username '$W1N' is supported.
            if not isinstance(username, str) or not re.fullmatch(r"[\w.@+$-]{3,150}", username, re.UNICODE):
                raise CommandError("Invalid developer username")
            if not isinstance(password, str) or len(password) < 12 or len(password) > 128:
                raise CommandError("Developer password length must be 12–128 characters")
            if not isinstance(job_title, str) or not job_title.strip() or len(job_title) > 80:
                raise CommandError("Invalid specialization")
            if username in seen:
                raise CommandError("Duplicate developer username")
            seen.add(username)
            cleaned.append((username, password, job_title.strip()))

        User = get_user_model()
        # Fail without changing any account if a requested name belongs to an administrator.
        for username, _, _ in cleaned:
            if User.objects.filter(username=username, is_superuser=True).exists():
                raise CommandError("Requested username belongs to a superuser")

        with transaction.atomic():
            # Lock roster rows to avoid inconsistent changes during this migration.
            retired = list(
                User.objects.select_for_update()
                .filter(dev_profile__role=Profile.Role.DEVELOPER, is_superuser=False)
                .exclude(username__in=seen)
            )
            for user in retired:
                if user.is_staff:
                    # Staff could be an administrator. Never revoke staff automatically.
                    continue
                if user.is_active:
                    user.is_active = False
                    user.save(update_fields=["is_active"])
                AppSession.objects.filter(user=user).delete()

            for username, password, job_title in cleaned:
                user = User.objects.select_for_update().filter(username=username).first()
                if user is None:
                    user = User(username=username)
                # Only a developer account, not a staff/admin account, may be updated.
                if user.pk is not None and (user.is_staff or user.is_superuser):
                    raise CommandError("Requested username belongs to an administrator")
                user.set_password(password)
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.save()
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.role = Profile.Role.DEVELOPER
                profile.job_title = job_title
                profile.save(update_fields=["role", "job_title"])
                AppSession.objects.filter(user=user).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Developer roster applied: {len(cleaned)} active, "
            f"{len([u for u in retired if not u.is_staff])} retired. "
            "Clear NIGHTWELL_REPLACE_DEVELOPERS_JSON."
        ))
