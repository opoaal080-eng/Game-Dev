from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("journal/", views.post_list, name="posts"),
    path("docs/", views.docs, name="docs"),
    path("journal/new/", views.post_create, name="post_create"),
    path("journal/<int:pk>/", views.post_detail, name="post_detail"),
    path("journal/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("tasks/", views.task_list, name="tasks"),
    path("tasks/new/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("files/", views.asset_list, name="assets"),
    path("files/new/", views.asset_create, name="asset_create"),
    path("files/<int:pk>/download/", views.asset_download, name="asset_download"),
    path("team/", views.team, name="team"),
    path("information/", views.information, name="information"),
    path("information/<int:pk>/edit/", views.information_edit, name="information_edit"),
    path("information/<int:pk>/events/new/", views.event_create, name="event_create"),
    path("information/events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("information/<int:pk>/characters/new/", views.character_create, name="character_create"),
    path("information/characters/<int:pk>/edit/", views.character_edit, name="character_edit"),
    path("search/", views.search, name="search"),
]
