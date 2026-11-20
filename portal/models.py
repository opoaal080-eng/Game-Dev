import os
import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Profile(models.Model):
    class Role(models.TextChoices):
        VIEWER = "viewer", "Наблюдатель"
        DEVELOPER = "developer", "Разработчик"
        ADMIN = "admin", "Администратор"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dev_profile")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.VIEWER)
    job_title = models.CharField("Специализация", max_length=80, blank=True)

    class Meta:
        verbose_name = "Роль участника"
        verbose_name_plural = "Роли участников"

    def __str__(self):
        return f"{self.user.username}: {self.get_role_display()}"


class Project(models.Model):
    title = models.CharField("Название", max_length=160)
    slug = models.SlugField(unique=True, max_length=160)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self):
        return self.title


class Post(models.Model):
    class Kind(models.TextChoices):
        DEVLOG = "devlog", "Дневник разработки"
        DOC = "doc", "Документация"
        NOTE = "note", "Заметка"
        MEETING = "meeting", "Встреча"
        DECISION = "decision", "Решение"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="posts", verbose_name="Проект")
    title = models.CharField("Заголовок", max_length=180)
    body = models.TextField("Содержание (Markdown)")
    kind = models.CharField("Тип", max_length=16, choices=Kind.choices, default=Kind.NOTE)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.DRAFT)
    pinned = models.BooleanField("Закрепить", default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="dev_posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-pinned", "-updated_at"]
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"

    def __str__(self):
        return self.title


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "К выполнению"
        PROGRESS = "progress", "В работе"
        REVIEW = "review", "На проверке"
        DONE = "done", "Готово"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        NORMAL = "normal", "Обычный"
        HIGH = "high", "Высокий"
        CRITICAL = "critical", "Срочно"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="tasks", verbose_name="Проект")
    title = models.CharField("Название", max_length=180)
    description = models.TextField("Описание", blank=True)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.TODO)
    priority = models.CharField("Приоритет", max_length=12, choices=Priority.choices, default=Priority.NORMAL)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_dev_tasks", verbose_name="Исполнитель")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_dev_tasks")
    due_date = models.DateField("Срок", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return self.title


def private_asset_path(instance, filename):
    # Randomized path avoids filename collisions, traversal and user input in storage paths.
    extension = Path(filename).suffix.lower()[:12]
    return f"assets/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{extension}"


class Asset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="assets", verbose_name="Проект")
    title = models.CharField("Название", max_length=180)
    description = models.TextField("Описание", blank=True)
    file = models.FileField("Файл", upload_to=private_asset_path, max_length=255)
    original_name = models.CharField("Исходное имя файла", max_length=255)
    size = models.PositiveBigIntegerField("Размер, байт", default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_dev_assets")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"

    def __str__(self):
        return self.title

    @property
    def download_name(self):
        return os.path.basename(self.original_name) or "attachment"
