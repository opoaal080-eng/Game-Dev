from django.test import TestCase
from django.urls import reverse


class NativeRoutesTests(TestCase):
    def test_api_requires_authorization(self):
        for name in ('native_me', 'native_dashboard', 'native_projects', 'native_posts', 'native_tasks', 'native_files', 'native_team'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 401)

    def test_game_information_requires_login(self):
        self.assertEqual(self.client.get(reverse('information')).status_code, 302)

    def test_event_and_character_forms_are_private(self):
        from .models import Project
        project = Project.objects.get(slug="main")
        self.assertEqual(self.client.get(reverse("event_create", args=(project.pk,))).status_code, 302)
        self.assertEqual(self.client.get(reverse("character_create", args=(project.pk,))).status_code, 302)

    def test_all_native_information_endpoints_are_protected(self):
        from .models import Project
        project = Project.objects.get(slug="main")
        self.assertEqual(self.client.get(reverse("native_information", args=(project.pk,))).status_code, 401)
        self.assertEqual(self.client.post(reverse("native_event_create", args=(project.pk,))).status_code, 401)
        self.assertEqual(self.client.post(reverse("native_character_create", args=(project.pk,))).status_code, 401)

    def test_native_login_and_revocation(self):
        import json
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user("api-tester", password="random-test-phrase-222333")
        response = self.client.post(
            reverse("native_login"),
            data=json.dumps({"username": user.username, "password": "random-test-phrase-222333"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        token = response.json()["token"]
        headers = {"HTTP_AUTHORIZATION": "Bearer " + token}
        self.assertEqual(self.client.get(reverse("native_me"), **headers).status_code, 200)
        self.assertEqual(self.client.post(reverse("native_logout"), **headers).status_code, 200)
        self.assertEqual(self.client.get(reverse("native_me"), **headers).status_code, 401)


    def test_github_pages_api_preflight_and_credentials(self):
        preflight = self.client.options(
            reverse("native_login"),
            HTTP_ORIGIN="https://opoaal080-eng.github.io",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )
        self.assertEqual(preflight.status_code, 204)
        self.assertEqual(preflight["Access-Control-Allow-Origin"], "https://opoaal080-eng.github.io")
        self.assertIn("Content-Type", preflight["Access-Control-Allow-Headers"])
        self.assertNotIn("Access-Control-Allow-Credentials", preflight)

        unauthorized = self.client.get(reverse("native_me"), HTTP_ORIGIN="https://opoaal080-eng.github.io")
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized["Access-Control-Allow-Origin"], "https://opoaal080-eng.github.io")

        other_site = self.client.get(reverse("native_me"), HTTP_ORIGIN="https://untrusted.example")
        self.assertEqual(other_site.status_code, 401)
        self.assertNotIn("Access-Control-Allow-Origin", other_site)
