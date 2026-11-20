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
