from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Asset, Post, Profile, Project, Task


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
