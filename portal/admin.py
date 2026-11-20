from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Asset, Post, Profile, Project, Task, GameInfo, GameEvent, GameCharacter, AppSession, PublicGamePage, PublicGameNews


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name_plural = "Доступ к порталу"


class PortalUserAdmin(UserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, PortalUserAdmin)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "kind", "status", "pinned", "author", "updated_at"]
    list_filter = ["project", "kind", "status"]
    search_fields = ["title", "body"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "status", "priority", "assignee", "due_date"]
    list_filter = ["project", "status", "priority"]
    search_fields = ["title", "description"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "uploaded_by", "size", "created_at"]
    list_filter = ["project"]


@admin.register(GameInfo)
class GameInfoAdmin(admin.ModelAdmin):
    list_display = ["project", "genre", "development_status", "updated_at"]
    search_fields = ["project__title", "title", "genre"]


@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "chapter", "kind", "order", "spoiler"]
    list_filter = ["project", "kind", "spoiler"]
    ordering = ["project", "order"]
    search_fields = ["title", "description", "summary"]


@admin.register(GameCharacter)
class GameCharacterAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "role", "faction", "order"]
    list_filter = ["project"]
    search_fields = ["name", "bio"]


@admin.register(AppSession)
class AppSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "device_name", "created_at", "expires_at", "last_used_at"]
    readonly_fields = ["user", "token_hash", "device_name", "created_at", "expires_at", "last_used_at"]
    list_filter = ["user"]
    def has_add_permission(self, request):
        return False


@admin.register(PublicGamePage)
class PublicGamePageAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "is_published", "genre", "updated_at"]
    list_filter = ["is_published"]
    readonly_fields = ["updated_at"]


@admin.register(PublicGameNews)
class PublicGameNewsAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "is_published", "published_at"]
    list_filter = ["is_published", "project"]
    search_fields = ["title", "summary"]
