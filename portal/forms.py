from django import forms
from django.core.exceptions import ValidationError
from .models import Asset, Post, Task, GameInfo, GameEvent, GameCharacter, PublicGamePage, PublicGameNews


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["project", "title", "kind", "status", "pinned", "content_mode", "code_language", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 14, "placeholder": "Заметки, ссылки, списки и решения команды…"})}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["project", "title", "description", "status", "priority", "assignee", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


MAX_UPLOAD_BYTES = 100 * 1024 * 1024


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["project", "title", "description", "file"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_file(self):
        upload = self.cleaned_data["file"]
        if upload.size > MAX_UPLOAD_BYTES:
            raise ValidationError("Размер файла не должен превышать 100 МБ")
        return upload


class GameInfoForm(forms.ModelForm):
    class Meta:
        model = GameInfo
        fields = ["title", "genre", "tagline", "setting", "story", "gameplay", "themes", "universe", "platforms", "engine", "development_status", "audience", "notes"]
        widgets = {name: forms.Textarea(attrs={"rows": 5}) for name in ("setting", "story", "gameplay", "themes", "universe", "notes")}


class GameEventForm(forms.ModelForm):
    class Meta:
        model = GameEvent
        fields = ["chapter", "title", "kind", "order", "timeline", "location", "participants", "summary", "description", "consequences", "spoiler"]
        widgets = {name: forms.Textarea(attrs={"rows": 4}) for name in ("summary", "description", "consequences")}


class GameCharacterForm(forms.ModelForm):
    class Meta:
        model = GameCharacter
        fields = ["name", "role", "faction", "bio", "motivation", "notes", "order"]
        widgets = {name: forms.Textarea(attrs={"rows": 4}) for name in ("bio", "motivation", "notes")}


class PublicGamePageForm(forms.ModelForm):
    class Meta:
        model = PublicGamePage
        fields = [
            "is_published", "title", "eyebrow", "tagline",
            "introduction", "story_teaser", "world_description", "feature_lines",
            "genre", "platforms", "development_status", "release_window",
            "hero_image_url", "trailer_url", "screenshots",
            "wishlist_url", "community_url", "telegram_url", "contact_email",
        ]
        widgets = {
            name: forms.Textarea(attrs={"rows": 5}) for name in (
                "introduction", "story_teaser", "world_description",
                "feature_lines", "screenshots",
            )
        }

    def clean(self):
        cleaned = super().clean()
        for name in (
            "hero_image_url", "trailer_url", "wishlist_url",
            "community_url", "telegram_url",
        ):
            value = cleaned.get(name)
            if value and not value.lower().startswith("https://"):
                self.add_error(name, "Для публичных ссылок нужен HTTPS.")
        gallery = cleaned.get("screenshots") or ""
        links = [line.strip() for line in gallery.splitlines() if line.strip()]
        if len(links) > 16:
            self.add_error("screenshots", "Не больше 16 изображений.")
        for value in links:
            try:
                validator = forms.URLField()
                validator.clean(value)
            except ValidationError:
                self.add_error("screenshots", "Некорректная ссылка на изображение.")
                break
            if not value.lower().startswith("https://"):
                self.add_error("screenshots", "Изображения должны загружаться по HTTPS.")
                break
        return cleaned


class PublicGameNewsForm(forms.ModelForm):
    class Meta:
        model = PublicGameNews
        fields = ["title", "summary", "content", "is_published"]
        widgets = {"content": forms.Textarea(attrs={"rows": 8})}
