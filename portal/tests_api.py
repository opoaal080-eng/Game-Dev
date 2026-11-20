from django.test import TestCase
from django.urls import reverse


class NativeRoutesTests(TestCase):
    def test_api_requires_authorization(self):
        for name in ('native_me', 'native_dashboard', 'native_projects', 'native_posts', 'native_tasks', 'native_files', 'native_team'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 401)

    def test_game_information_requires_login(self):
        self.assertEqual(self.client.get(reverse('information')).status_code, 302)
