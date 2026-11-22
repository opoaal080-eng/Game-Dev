import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import GameInfo, Post, Profile, Project, PublicGamePage, PublicGameNews


class AshfallPublicSiteTests(TestCase):
    def setUp(self):
        self.project = Project.objects.get(slug="main")
        self.page = PublicGamePage.objects.get(project=self.project)
        self.page.title = "ASHFALL"
        self.page.is_published = True
        self.page.genre = "Тестовый жанр"
        self.page.story_teaser = "Публичная завязка без спойлеров"
        self.page.save()
        self.secret = "SECRET_PRIVATE_PLOT_291"
        GameInfo.objects.update_or_create(
            project=self.project, defaults={"story": self.secret}
        )
        self.developer = get_user_model().objects.create_user(
            username="ashfall-dev", password="StrongTestPassword2026"
        )
        profile, _ = Profile.objects.get_or_create(user=self.developer)
        profile.role = Profile.Role.DEVELOPER
        profile.save()
        self.viewer = get_user_model().objects.create_user(
            username="ashfall-reader", password="StrongTestPassword2026"
        )
        PublicGameNews.objects.create(
            project=self.project, title="Публичная новость",
            content="Для игроков", is_published=True,
        )
        PublicGameNews.objects.create(
            project=self.project, title="НЕПУБЛИЧНЫЙ ЧЕРНОВИК 123",
            content="Только разработчики", is_published=False,
        )

    def test_public_api_never_leaks_private_materials(self):
        response = self.client.get(reverse("public_ashfall_data"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertIn("public", response["Cache-Control"])
        data = response.json()
        self.assertEqual(data["title"], "ASHFALL")
        self.assertEqual(data["eyebrow"], "NIGHTWELL STUDIO · ИГРОВОЙ ПРОЕКТ")
        self.assertEqual(data["genre"], "Тестовый жанр")
        self.assertEqual(len(data["news"]), 1)
        self.assertNotIn(self.secret, response.content.decode())
        self.assertNotIn("НЕПУБЛИЧНЫЙ ЧЕРНОВИК", response.content.decode())

    def test_private_editor_and_tokens(self):
        self.assertEqual(self.client.get(reverse("player_site_editor")).status_code, 302)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("player_site_editor")).status_code, 403)
        self.client.force_login(self.developer)
        self.assertEqual(self.client.get(reverse("player_site_editor")).status_code, 200)
        response = self.client.post(reverse("player_site_editor"), data={
            "is_published": "on", "title": "ASHFALL", "tagline": "Новый анонс",
        })
        self.assertEqual(response.status_code, 302)
        self.page.refresh_from_db()
        self.assertEqual(self.page.tagline, "Новый анонс")

    def test_draft_site_hides_all_game_data_and_news(self):
        self.page.is_published = False
        self.page.save()
        data = self.client.get(reverse("public_ashfall_data")).json()
        self.assertFalse(data["published"])
        self.assertEqual(data["title"], "ASHFALL")
        self.assertFalse(data["news"])
        self.assertNotIn(self.page.genre, json.dumps(data, ensure_ascii=False))

    def test_custom_domain_root_is_public_and_dev_root_private(self):
        response = self.client.get("/", HTTP_HOST="afl.nightwell.fun")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ASHFALL", response.content)
        self.assertEqual(
            self.client.get("/").status_code,
            302
        )

    def test_https_required_for_public_media(self):
        self.client.force_login(self.developer)
        response = self.client.post(reverse("player_site_editor"), data={
            "title": "ASHFALL", "is_published": "on",
            "hero_image_url": "http://insecure.example/cover.png"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HTTPS")

    def test_private_api_reader_cannot_edit(self):
        token = self._login_token(self.viewer)
        response = self.client.put(
            reverse("native_player_site"),
            data=json.dumps({"title": "Secret overwrite"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer " + token,
        )
        self.assertEqual(response.status_code, 403)

    def test_private_api_developer_can_update_published_info(self):
        token = self._login_token(self.developer)
        response = self.client.put(
            reverse("native_player_site"),
            data=json.dumps({"title": "ASHFALL", "tagline": "Новый слоган"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer " + token,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.page.refresh_from_db()
        self.assertEqual(self.page.tagline, "Новый слоган")
        self.assertEqual(
            self.client.get(reverse("public_ashfall_data")).json()["tagline"],
            "Новый слоган",
        )

    def _login_token(self, user):
        response = self.client.post(
            reverse("native_login"),
            data=json.dumps({"username": user.username, "password": "StrongTestPassword2026"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["token"]
