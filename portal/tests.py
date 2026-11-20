"""Access and workflow tests. Run: python manage.py test"""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Asset, Post, Profile, Project, Task

User = get_user_model()


class PortalAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.get(slug="main")
        cls.viewer = User.objects.create_user("viewer", password="strong test password 123")
        cls.developer = User.objects.create_user("developer", password="strong test password 123")
        cls.other = User.objects.create_user("otherdev", password="strong test password 123")
        cls.admin = User.objects.create_superuser("chief", "chief@example.test", "strong test password 123")
        cls.developer.dev_profile.role = Profile.Role.DEVELOPER
        cls.developer.dev_profile.save()
        cls.other.dev_profile.role = Profile.Role.DEVELOPER
        cls.other.dev_profile.save()
        cls.published = Post.objects.create(project=cls.project, title="Public team note", body="some text", status="published", author=cls.developer)
        cls.draft = Post.objects.create(project=cls.project, title="Secret draft", body="internal", status="draft", author=cls.developer)
        cls.doc = Post.objects.create(project=cls.project, title="Technical doc", body="## Section", kind="doc", status="published", author=cls.developer)
        cls.task = Task.objects.create(project=cls.project, title="First task", created_by=cls.developer)

    def test_private_pages_redirect_guests(self):
        urls = ["dashboard", "posts", "docs", "tasks", "assets", "team", "search", "post_create", "task_create", "asset_create"]
        for name in urls:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login/", response.url)

    def test_viewer_does_not_see_drafts(self):
        self.client.force_login(self.viewer)
        self.assertContains(self.client.get(reverse("posts")), "Public team note")
        self.assertNotContains(self.client.get(reverse("posts")), "Secret draft")
        self.assertEqual(self.client.get(reverse("post_detail", args=[self.draft.pk])).status_code, 404)
        self.assertContains(self.client.get(reverse("docs")), "Technical doc")
        self.assertNotContains(self.client.get(reverse("docs")), "Public team note")

    def test_developer_sees_draft_and_can_publish(self):
        self.client.force_login(self.developer)
        self.assertContains(self.client.get(reverse("posts")), "Secret draft")
        response = self.client.post(reverse("post_create"), {"project": self.project.pk, "title": "Build report", "kind": "devlog", "status": "published", "body": "Content"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title="Build report").exists())

    def test_viewer_cannot_write(self):
        self.client.force_login(self.viewer)
        for name in ["post_create", "task_create", "asset_create"]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_non_owner_cannot_edit_other_post(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("post_edit", args=[self.published.pk])).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("post_edit", args=[self.published.pk])).status_code, 200)

    def test_task_cannot_be_edited_by_unrelated_developer(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("task_edit", args=[self.task.pk])).status_code, 403)

    def test_no_public_registration(self):
        self.assertEqual(self.client.get("/register/").status_code, 404)

    def test_developer_can_change_own_password(self):
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 302)
        self.client.force_login(self.developer)
        response = self.client.post(reverse("password_change"), {
            "old_password": "strong test password 123",
            "new_password1": "new powerful password 456 789",
            "new_password2": "new powerful password 456 789",
        })
        self.assertRedirects(response, reverse("password_change_done"))
        self.developer.refresh_from_db()
        self.assertTrue(self.developer.check_password("new powerful password 456 789"))
        self.assertEqual(self.client.get(reverse("password_change_done")).status_code, 200)



class PrivateFilesTests(TestCase):
    def setUp(self):
        self.temporary_files = tempfile.mkdtemp(prefix="nightwell-test-")
        self.override = override_settings(MEDIA_ROOT=self.temporary_files)
        self.override.enable()
        self.user = User.objects.create_user("editor", password="strong test password 123")
        self.user.dev_profile.role = Profile.Role.DEVELOPER
        self.user.dev_profile.save()
        self.project = Project.objects.get(slug="main")

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temporary_files, ignore_errors=True)

    def test_file_requires_login_and_downloads_as_attachment(self):
        self.client.force_login(self.user)
        content = b"private engineering notes"
        response = self.client.post(reverse("asset_create"), {
            "project": self.project.pk, "title": "Internal file", "description": "", "file": SimpleUploadedFile("notes.txt", content, content_type="text/plain"),
        })
        self.assertEqual(response.status_code, 302)
        asset = Asset.objects.get(title="Internal file")
        url = reverse("asset_download", args=[asset.pk])
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.user)
        download = self.client.get(url)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), content)
        self.assertEqual(download["Content-Type"], "application/octet-stream")
        self.assertIn("attachment", download["Content-Disposition"])
        self.assertEqual(self.client.get("/not-publicly-served/" + asset.file.name).status_code, 404)

    def test_extension_filter(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("asset_create"), {
            "project": self.project.pk, "title": "Unsafe file", "description": "", "file": SimpleUploadedFile("script.exe", b"malware"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "формат файла пока не разрешён")
        self.assertFalse(Asset.objects.filter(title="Unsafe file").exists())
