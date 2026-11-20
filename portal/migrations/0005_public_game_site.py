from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

def seed_ashfall(apps, schema_editor):
    Project = apps.get_model("portal", "Project")
    Page = apps.get_model("portal", "PublicGamePage")
    main = Project.objects.filter(slug="main").first()
    if main:
        Page.objects.get_or_create(project=main, defaults={
            "title": "ASHFALL",
            "eyebrow": "NIGHTWELL · ИГРОВОЙ ПРОЕКТ",
            "is_published": True,
        })

class Migration(migrations.Migration):
    dependencies = [("portal", "0004_game_information")]
    operations = [
        migrations.CreateModel(
            name="PublicGamePage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_published", models.BooleanField(default=False, verbose_name="Сайт опубликован")),
                ("title", models.CharField(default="ASHFALL", max_length=160, verbose_name="Название игры")),
                ("eyebrow", models.CharField(blank=True, max_length=120, verbose_name="Надпись над названием")),
                ("tagline", models.CharField(blank=True, max_length=240, verbose_name="Слоган")),
                ("introduction", models.TextField(blank=True, verbose_name="Описание для игроков")),
                ("story_teaser", models.TextField(blank=True, verbose_name="Завязка сюжета без спойлеров")),
                ("world_description", models.TextField(blank=True, verbose_name="Мир игры для игроков")),
                ("feature_lines", models.TextField(blank=True, verbose_name="Особенности, одна на строку")),
                ("genre", models.CharField(blank=True, max_length=200, verbose_name="Жанр")),
                ("platforms", models.CharField(blank=True, max_length=180, verbose_name="Платформы")),
                ("development_status", models.CharField(blank=True, max_length=120, verbose_name="Этап разработки")),
                ("release_window", models.CharField(blank=True, max_length=120, verbose_name="Дата или период релиза")),
                ("hero_image_url", models.URLField(blank=True, max_length=600, verbose_name="Главное изображение, HTTPS")),
                ("trailer_url", models.URLField(blank=True, max_length=600, verbose_name="Трейлер или видео, HTTPS")),
                ("screenshots", models.TextField(blank=True, verbose_name="Скриншоты, HTTPS-ссылки по одной в строке")),
                ("community_url", models.URLField(blank=True, max_length=600, verbose_name="Сообщество, HTTPS")),
                ("telegram_url", models.URLField(blank=True, max_length=600, verbose_name="Telegram, HTTPS")),
                ("wishlist_url", models.URLField(blank=True, max_length=600, verbose_name="Страница игры в магазине, HTTPS")),
                ("contact_email", models.EmailField(blank=True, max_length=254, verbose_name="Email для связи")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="public_page", to="portal.project")),
            ],
            options={"verbose_name": "Публичный сайт игры", "verbose_name_plural": "Публичные сайты игр"},
        ),
        migrations.CreateModel(
            name="PublicGameNews",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="Заголовок новости")),
                ("summary", models.CharField(blank=True, max_length=320, verbose_name="Краткое описание")),
                ("content", models.TextField(blank=True, verbose_name="Текст для игроков")),
                ("is_published", models.BooleanField(default=False, verbose_name="Показать игрокам")),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата публикации")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="public_news", to="portal.project")),
            ],
            options={"ordering": ["-published_at", "-id"], "verbose_name": "Публичная новость", "verbose_name_plural": "Публичные новости"},
        ),
        migrations.RunPython(seed_ashfall, migrations.RunPython.noop),
    ]
