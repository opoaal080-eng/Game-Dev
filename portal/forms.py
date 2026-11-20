from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from .models import Asset, Post, Task


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["project", "title", "kind", "status", "pinned", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 14, "placeholder": "Заметки, ссылки, списки и решения команды…"})}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["project", "title", "description", "status", "priority", "assignee", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".json", ".csv", ".zip", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".psd", ".kra",
    ".glb", ".gltf", ".obj", ".fbx", ".blend", ".unity", ".prefab",
    ".wav", ".mp3", ".ogg", ".mp4", ".mov", ".webm", ".cs", ".py",
    ".shader", ".hlsl", ".gd", ".ts", ".js", ".yml", ".yaml",
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
        if Path(upload.name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValidationError("Этот формат файла пока не разрешён")
        return upload
