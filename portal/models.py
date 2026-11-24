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

    class ContentMode(models.TextChoices):
        MARKDOWN = "markdown", "Текст и Markdown"
        CODE = "code", "Скрипт целиком"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="posts", verbose_name="Проект")
    title = models.CharField("Заголовок", max_length=180)
    body = models.TextField("Содержание (Markdown)")
    kind = models.CharField("Тип", max_length=16, choices=Kind.choices, default=Kind.NOTE)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.DRAFT)
    pinned = models.BooleanField("Закрепить", default=False)
    content_mode = models.CharField("Формат содержимого", max_length=12, choices=ContentMode.choices, default=ContentMode.MARKDOWN)
    code_language = models.CharField("Язык кода", max_length=32, blank=True, default="")
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


class AppSession(models.Model):
    """Revocable native-app access token. Only its SHA-256 digest is stored."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="native_sessions")
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    device_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Сессия приложения"
        verbose_name_plural = "Сессии приложений"

    def __str__(self):
        return f"{self.user.username} · {self.device_name or 'Устройство'}"


class GameInfo(models.Model):
    """Creative bible of a game: one per project."""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="game_info")
    genre = models.CharField("Жанр", max_length=240, blank=True)
    title = models.CharField("Рабочее название игры", max_length=160, blank=True)
    tagline = models.CharField("Короткое описание", max_length=300, blank=True)
    setting = models.TextField("Мир и сеттинг", blank=True)
    story = models.TextField("Сюжет", blank=True)
    gameplay = models.TextField("Геймплей и механики", blank=True)
    themes = models.TextField("Темы и атмосфера", blank=True)
    universe = models.TextField("Лор и предыстория", blank=True)
    platforms = models.CharField("Платформы", max_length=200, blank=True)
    engine = models.CharField("Движок", max_length=100, blank=True)
    development_status = models.CharField("Стадия разработки", max_length=120, blank=True)
    audience = models.CharField("Аудитория и возрастной рейтинг", max_length=180, blank=True)
    notes = models.TextField("Прочая информация", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Информация об игре"
        verbose_name_plural = "Информация об играх"

    def __str__(self):
        return f"Информация: {self.project.title}"


class GameEvent(models.Model):
    class Kind(models.TextChoices):
        MAIN = "main", "Основное событие"
        SIDE = "side", "Побочное событие"
        BACKSTORY = "backstory", "Предыстория"
        OPTIONAL = "optional", "Необязательное событие"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="game_events")
    chapter = models.CharField("Глава или акт", max_length=120, blank=True)
    title = models.CharField("Название события", max_length=180)
    kind = models.CharField("Тип", max_length=16, choices=Kind.choices, default=Kind.MAIN)
    order = models.PositiveIntegerField("Порядок событий", default=1)
    timeline = models.CharField("Время в сюжете", max_length=120, blank=True)
    location = models.CharField("Место действия", max_length=200, blank=True)
    participants = models.CharField("Участники", max_length=300, blank=True)
    summary = models.TextField("Краткое содержание", blank=True)
    description = models.TextField("Подробное описание", blank=True)
    consequences = models.TextField("Последствия и развилки", blank=True)
    spoiler = models.BooleanField("Содержит спойлеры", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = "Сюжетное событие"
        verbose_name_plural = "Сюжетные события"

    def __str__(self):
        return self.title


class GameCharacter(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="game_characters")
    name = models.CharField("Имя персонажа", max_length=160)
    role = models.CharField("Роль в истории", max_length=160, blank=True)
    faction = models.CharField("Фракция или организация", max_length=160, blank=True)
    bio = models.TextField("Биография", blank=True)
    motivation = models.TextField("Мотивация и цели", blank=True)
    notes = models.TextField("Прочее", blank=True)
    order = models.PositiveIntegerField("Порядок", default=1)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = "Персонаж игры"
        verbose_name_plural = "Персонажи игр"

    def __str__(self):
        return self.name


class PublicGamePage(models.Model):
    """Curated information for players, never a public mirror of private GameInfo."""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="public_page")
    is_published = models.BooleanField("Сайт опубликован", default=False)
    title = models.CharField("Название игры", max_length=160, default="ASHFALL")
    eyebrow = models.CharField("Надпись над названием", max_length=120, blank=True)
    tagline = models.CharField("Слоган", max_length=240, blank=True)
    introduction = models.TextField("Описание для игроков", blank=True)
    story_teaser = models.TextField("Завязка сюжета без спойлеров", blank=True)
    world_description = models.TextField("Мир игры для игроков", blank=True)
    feature_lines = models.TextField("Особенности, одна на строку", blank=True)
    genre = models.CharField("Жанр", max_length=200, blank=True)
    platforms = models.CharField("Платформы", max_length=180, blank=True)
    development_status = models.CharField("Этап разработки", max_length=120, blank=True)
    release_window = models.CharField("Дата или период релиза", max_length=120, blank=True)
    hero_image_url = models.URLField("Главное изображение, HTTPS", max_length=600, blank=True)
    trailer_url = models.URLField("Трейлер или видео, HTTPS", max_length=600, blank=True)
    screenshots = models.TextField("Скриншоты, HTTPS-ссылки по одной в строке", blank=True)
    community_url = models.URLField("Сообщество, HTTPS", max_length=600, blank=True)
    telegram_url = models.URLField("Telegram, HTTPS", max_length=600, blank=True)
    wishlist_url = models.URLField("Страница игры в магазине, HTTPS", max_length=600, blank=True)
    contact_email = models.EmailField("Email для связи", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Публичный сайт игры"
        verbose_name_plural = "Публичные сайты игр"

    def __str__(self):
        return f"{self.title} · {'опубликовано' if self.is_published else 'черновик'}"


class PublicGameNews(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="public_news")
    title = models.CharField("Заголовок новости", max_length=180)
    summary = models.CharField("Краткое описание", max_length=320, blank=True)
    content = models.TextField("Текст для игроков", blank=True)
    is_published = models.BooleanField("Показать игрокам", default=False)
    published_at = models.DateTimeField("Дата публикации", default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-id"]
        verbose_name = "Публичная новость"
        verbose_name_plural = "Публичные новости"

    def __str__(self):
        return self.title
