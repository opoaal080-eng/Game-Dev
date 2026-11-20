from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("portal", "0003_appsession")]
    operations = [
        migrations.CreateModel(
            name="GameInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("genre", models.CharField(blank=True, max_length=240, verbose_name="Жанр")),
                ("title", models.CharField(blank=True, max_length=160, verbose_name="Рабочее название игры")),
                ("tagline", models.CharField(blank=True, max_length=300, verbose_name="Короткое описание")),
                ("setting", models.TextField(blank=True, verbose_name="Мир и сеттинг")),
                ("story", models.TextField(blank=True, verbose_name="Сюжет")),
                ("gameplay", models.TextField(blank=True, verbose_name="Геймплей и механики")),
                ("themes", models.TextField(blank=True, verbose_name="Темы и атмосфера")),
                ("universe", models.TextField(blank=True, verbose_name="Лор и предыстория")),
                ("platforms", models.CharField(blank=True, max_length=200, verbose_name="Платформы")),
                ("engine", models.CharField(blank=True, max_length=100, verbose_name="Движок")),
                ("development_status", models.CharField(blank=True, max_length=120, verbose_name="Стадия разработки")),
                ("audience", models.CharField(blank=True, max_length=180, verbose_name="Аудитория и возрастной рейтинг")),
                ("notes", models.TextField(blank=True, verbose_name="Прочая информация")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="game_info", to="portal.project")),
            ],
            options={"verbose_name": "Информация об игре", "verbose_name_plural": "Информация об играх"},
        ),
        migrations.CreateModel(
            name="GameEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chapter", models.CharField(blank=True, max_length=120, verbose_name="Глава или акт")),
                ("title", models.CharField(max_length=180, verbose_name="Название события")),
                ("kind", models.CharField(choices=[("main", "Основное событие"), ("side", "Побочное событие"), ("backstory", "Предыстория"), ("optional", "Необязательное событие")], default="main", max_length=16, verbose_name="Тип")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="Порядок событий")),
                ("timeline", models.CharField(blank=True, max_length=120, verbose_name="Время в сюжете")),
                ("location", models.CharField(blank=True, max_length=200, verbose_name="Место действия")),
                ("participants", models.CharField(blank=True, max_length=300, verbose_name="Участники")),
                ("summary", models.TextField(blank=True, verbose_name="Краткое содержание")),
                ("description", models.TextField(blank=True, verbose_name="Подробное описание")),
                ("consequences", models.TextField(blank=True, verbose_name="Последствия и развилки")),
                ("spoiler", models.BooleanField(default=False, verbose_name="Содержит спойлеры")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="game_events", to="portal.project")),
            ],
            options={"ordering": ["order", "pk"], "verbose_name": "Сюжетное событие", "verbose_name_plural": "Сюжетные события"},
        ),
        migrations.CreateModel(
            name="GameCharacter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Имя персонажа")),
                ("role", models.CharField(blank=True, max_length=160, verbose_name="Роль в истории")),
                ("faction", models.CharField(blank=True, max_length=160, verbose_name="Фракция или организация")),
                ("bio", models.TextField(blank=True, verbose_name="Биография")),
                ("motivation", models.TextField(blank=True, verbose_name="Мотивация и цели")),
                ("notes", models.TextField(blank=True, verbose_name="Прочее")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="Порядок")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="game_characters", to="portal.project")),
            ],
            options={"ordering": ["order", "pk"], "verbose_name": "Персонаж игры", "verbose_name_plural": "Персонажи игр"},
        ),
    ]
