# Initial schema for Nightwell Dev, Django 5.2.
import django.db.models.deletion
import portal.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="Название")),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["title"], "verbose_name": "Проект", "verbose_name_plural": "Проекты"},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("viewer", "Наблюдатель"), ("developer", "Разработчик"), ("admin", "Администратор")], default="viewer", max_length=12)),
                ("job_title", models.CharField(blank=True, max_length=80, verbose_name="Специализация")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="dev_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Роль участника", "verbose_name_plural": "Роли участников"},
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="Заголовок")),
                ("body", models.TextField(verbose_name="Содержание (Markdown)")),
                ("kind", models.CharField(choices=[("devlog", "Дневник разработки"), ("doc", "Документация"), ("note", "Заметка"), ("meeting", "Встреча"), ("decision", "Решение")], default="note", max_length=16, verbose_name="Тип")),
                ("status", models.CharField(choices=[("draft", "Черновик"), ("published", "Опубликовано")], default="draft", max_length=12, verbose_name="Статус")),
                ("pinned", models.BooleanField(default=False, verbose_name="Закрепить")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dev_posts", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="posts", to="portal.project", verbose_name="Проект")),
            ],
            options={"ordering": ["-pinned", "-updated_at"], "verbose_name": "Публикация", "verbose_name_plural": "Публикации"},
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("status", models.CharField(choices=[("todo", "К выполнению"), ("progress", "В работе"), ("review", "На проверке"), ("done", "Готово")], default="todo", max_length=12, verbose_name="Статус")),
                ("priority", models.CharField(choices=[("low", "Низкий"), ("normal", "Обычный"), ("high", "Высокий"), ("critical", "Срочно")], default="normal", max_length=12, verbose_name="Приоритет")),
                ("due_date", models.DateField(blank=True, null=True, verbose_name="Срок")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assignee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_dev_tasks", to=settings.AUTH_USER_MODEL, verbose_name="Исполнитель")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_dev_tasks", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tasks", to="portal.project", verbose_name="Проект")),
            ],
            options={"ordering": ["-updated_at"], "verbose_name": "Задача", "verbose_name_plural": "Задачи"},
        ),
        migrations.CreateModel(
            name="Asset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("file", models.FileField(max_length=255, upload_to=portal.models.private_asset_path, verbose_name="Файл")),
                ("original_name", models.CharField(max_length=255, verbose_name="Исходное имя файла")),
                ("size", models.PositiveBigIntegerField(default=0, verbose_name="Размер, байт")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assets", to="portal.project", verbose_name="Проект")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_dev_assets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "Материал", "verbose_name_plural": "Материалы"},
        ),
    ]
