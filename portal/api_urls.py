from django.urls import path
from . import api

urlpatterns = [
    path("auth/login/", api.login, name="native_login"),
    path("auth/logout/", api.logout, name="native_logout"),
    path("auth/password/", api.change_password, name="native_change_password"),
    path("me/", api.me, name="native_me"),
    path("dashboard/", api.dashboard, name="native_dashboard"),
    path("projects/", api.projects, name="native_projects"),
    path("posts/", api.posts, name="native_posts"),
    path("posts/<int:pk>/", api.post_detail, name="native_post_detail"),
    path("tasks/", api.tasks, name="native_tasks"),
    path("tasks/<int:pk>/", api.task_detail, name="native_task_detail"),
    path("files/", api.files, name="native_files"),
    path("files/<int:pk>/download/", api.file_download, name="native_file_download"),
    path("team/", api.team, name="native_team"),
]
