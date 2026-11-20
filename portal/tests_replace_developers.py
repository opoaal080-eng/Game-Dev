import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.core.management.base import CommandError

from portal.models import AppSession, Post, Profile, Project


class ReplaceDevelopersTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("root-operator", "example@example.com", "SafeTestPassword009")
        self.old = User.objects.create_user("former-dev", password="OldTestPassword009")
        self.old.dev_profile.role = Profile.Role.DEVELOPER
        self.old.dev_profile.save()
        self.project = Project.objects.get(slug="main")
        self.post = Post.objects.create(
            project=self.project, title="Archived authored work", body="Preserved history",
            kind=Post.Kind.NOTE, status=Post.Status.PUBLISHED, author=self.old,
        )

    def roster(self):
        return [
            {"username": "konl1ght", "password": "mock-password-one-123", "job_title": "Game-дизайнер, сценарист"},
            {"username": "$W1N", "password": "mock-password-two-123", "job_title": "Веб-кодер, UI/UX"},
            {"username": "nemesxs", "password": "mock-password-three-123", "job_title": "Художник-аниматор"},
        ]

    def test_replace_three_without_deleting_history_or_superuser(self):
        with patch.dict("os.environ", {"NIGHTWELL_REPLACE_DEVELOPERS_JSON": json.dumps(self.roster())}):
            call_command("replace_developers")
            call_command("replace_developers")

        User = get_user_model()
        self.old.refresh_from_db()
        self.assertFalse(self.old.is_active)
        self.assertTrue(User.objects.get(username=self.admin.username).is_superuser)
        self.assertEqual(Post.objects.get(pk=self.post.pk).author_id, self.old.pk)
        for record in self.roster():
            user = User.objects.get(username=record["username"])
            self.assertTrue(user.is_active)
            self.assertFalse(user.is_staff)
            self.assertTrue(user.check_password(record["password"]))
            self.assertEqual(user.dev_profile.role, Profile.Role.DEVELOPER)
            self.assertEqual(user.dev_profile.job_title, record["job_title"])

    def test_admin_collision_refuses_without_disabling_old_developers(self):
        records = self.roster()
        records[0]["username"] = self.admin.username
        with patch.dict("os.environ", {"NIGHTWELL_REPLACE_DEVELOPERS_JSON": json.dumps(records)}):
            with self.assertRaises(CommandError):
                call_command("replace_developers")
        self.old.refresh_from_db()
        self.assertTrue(self.old.is_active)
