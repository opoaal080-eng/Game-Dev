from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .access import can_write, is_admin, require_owner_or_admin, require_writer
from .forms import AssetForm, PostForm, TaskForm, GameInfoForm, GameEventForm, GameCharacterForm
from .models import Asset, Post, Project, Task, GameInfo, GameEvent, GameCharacter


def visible_posts(user):
    queryset = Post.objects.select_related("project", "author")
    if not can_write(user):
        queryset = queryset.filter(status=Post.Status.PUBLISHED)
    return queryset


@login_required
@require_GET
def dashboard(request):
    posts = visible_posts(request.user)
    tasks = Task.objects.select_related("project", "assignee")
    context = {
        "projects": Project.objects.all()[:6],
        "latest_posts": posts[:5],
        "active_tasks": tasks.exclude(status=Task.Status.DONE)[:6],
        "latest_assets": Asset.objects.select_related("project", "uploaded_by")[:5],
        "post_count": posts.count(),
        "task_count": tasks.exclude(status=Task.Status.DONE).count(),
        "asset_count": Asset.objects.count(),
        "member_count": get_user_model().objects.filter(is_active=True).count(),
    }
    return render(request, "portal/dashboard.html", context)


@login_required
@require_GET
def post_list(request):
    posts = visible_posts(request.user).exclude(kind=Post.Kind.DOC)
    selected_kind = request.GET.get("kind", "")
    if selected_kind in Post.Kind.values:
        posts = posts.filter(kind=selected_kind)
    selected_project = request.GET.get("project", "")
    if selected_project.isdigit():
        posts = posts.filter(project_id=int(selected_project))
    return render(request, "portal/post_list.html", {
        "posts": posts[:100],
        "kinds": Post.Kind.choices,
        "projects": Project.objects.all(),
        "selected_kind": selected_kind,
        "selected_project": selected_project,
        "page_title": "Дневник разработки",
        "page_label": "ХОД РАЗРАБОТКИ",
        "page_description": "Заметки разработчиков, решения, встречи и обновления проекта.",
        "docs_mode": False,
    })


@login_required
@require_GET
def docs(request):
    posts = visible_posts(request.user).filter(kind=Post.Kind.DOC)
    selected_project = request.GET.get("project", "")
    if selected_project.isdigit():
        posts = posts.filter(project_id=int(selected_project))
    return render(request, "portal/post_list.html", {
        "posts": posts[:100],
        "projects": Project.objects.all(),
        "selected_project": selected_project,
        "page_title": "Документация",
        "page_label": "БАЗА ЗНАНИЙ",
        "page_description": "Инструкции, спецификации, технические решения и документация.",
        "docs_mode": True,
    })


@login_required
@require_GET
def post_detail(request, pk):
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    return render(request, "portal/post_detail.html", {
        "post": post,
        "may_edit": can_write(request.user) and (is_admin(request.user) or post.author_id == request.user.pk),
    })


@login_required
@require_http_methods(["GET", "POST"])
def post_create(request):
    require_writer(request.user)
    form = PostForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Публикация сохранена")
        return redirect("post_detail", pk=post.pk)
    return render(request, "portal/editor.html", {"form": form, "title": "Новая публикация", "section": "notes"})


@login_required
@require_http_methods(["GET", "POST"])
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    require_owner_or_admin(request.user, post.author_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Изменения сохранены")
        return redirect("post_detail", pk=post.pk)
    return render(request, "portal/editor.html", {"form": form, "title": "Редактирование публикации", "section": "notes"})


@login_required
@require_GET
def task_list(request):
    tasks = Task.objects.select_related("project", "assignee", "created_by")
    selected_project = request.GET.get("project", "")
    if selected_project.isdigit():
        tasks = tasks.filter(project_id=int(selected_project))
    return render(request, "portal/task_list.html", {
        "columns": [(status, label, tasks.filter(status=status)[:60]) for status, label in Task.Status.choices],
        "projects": Project.objects.all(),
        "selected_project": selected_project,
    })


@login_required
@require_http_methods(["GET", "POST"])
def task_create(request):
    require_writer(request.user)
    form = TaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.created_by = request.user
        task.save()
        messages.success(request, "Задача создана")
        return redirect("tasks")
    return render(request, "portal/editor.html", {"form": form, "title": "Новая задача", "section": "tasks"})


@login_required
@require_http_methods(["GET", "POST"])
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    require_writer(request.user)
    if not (is_admin(request.user) or task.created_by_id == request.user.pk or task.assignee_id == request.user.pk):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Редактировать задачу может автор, исполнитель или администратор")
    form = TaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Задача обновлена")
        return redirect("tasks")
    return render(request, "portal/editor.html", {"form": form, "title": "Редактирование задачи", "section": "tasks"})


@login_required
@require_GET
def asset_list(request):
    assets = Asset.objects.select_related("project", "uploaded_by")
    selected_project = request.GET.get("project", "")
    if selected_project.isdigit():
        assets = assets.filter(project_id=int(selected_project))
    return render(request, "portal/asset_list.html", {
        "assets": assets[:100], "projects": Project.objects.all(), "selected_project": selected_project,
    })


@login_required
@require_http_methods(["GET", "POST"])
def asset_create(request):
    require_writer(request.user)
    form = AssetForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        asset = form.save(commit=False)
        upload = form.cleaned_data["file"]
        asset.original_name = upload.name[:255]
        asset.size = upload.size
        asset.uploaded_by = request.user
        asset.save()
        messages.success(request, "Файл загружен в закрытое хранилище")
        return redirect("assets")
    return render(request, "portal/editor.html", {
        "form": form, "title": "Добавить материал", "section": "assets", "file_form": True,
    })


@login_required
@never_cache
@require_GET
def asset_download(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    try:
        stored_file = asset.file.open("rb")
    except (OSError, FileNotFoundError):
        raise Http404("Файл не найден")
    return FileResponse(stored_file, as_attachment=True, filename=asset.download_name, content_type="application/octet-stream")


@login_required
@require_GET
def team(request):
    members = get_user_model().objects.filter(is_active=True).select_related("dev_profile").order_by("first_name", "username")
    return render(request, "portal/team.html", {"members": members})


@login_required
@require_GET
def search(request):
    term = request.GET.get("q", "").strip()[:120]
    posts = visible_posts(request.user).none()
    tasks = Task.objects.none()
    assets = Asset.objects.none()
    if term:
        posts = visible_posts(request.user).filter(Q(title__icontains=term) | Q(body__icontains=term))[:30]
        tasks = Task.objects.select_related("project").filter(Q(title__icontains=term) | Q(description__icontains=term))[:30]
        assets = Asset.objects.select_related("project").filter(Q(title__icontains=term) | Q(description__icontains=term))[:30]
    return render(request, "portal/search.html", {"term": term, "posts": posts, "tasks": tasks, "assets": assets})


@login_required
@require_GET
def information(request):
    projects = Project.objects.all().order_by("title")
    selected_id = request.GET.get("project", "")
    project = projects.filter(pk=int(selected_id)).first() if selected_id.isdigit() else projects.first()
    if not project:
        raise Http404("Проекты не найдены")
    info = GameInfo.objects.filter(project=project).first()
    events = GameEvent.objects.filter(project=project).order_by("order", "pk")
    characters = GameCharacter.objects.filter(project=project).order_by("order", "pk")
    return render(request, "portal/information.html", {
        "projects": projects, "project": project, "info": info,
        "events": events, "characters": characters,
    })


@login_required
@require_http_methods(["GET", "POST"])
def information_edit(request, pk):
    require_writer(request.user)
    project = get_object_or_404(Project, pk=pk)
    info, _ = GameInfo.objects.get_or_create(project=project)
    form = GameInfoForm(request.POST or None, instance=info)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Информация об игре обновлена")
        return redirect(f"/information/?project={project.pk}")
    return render(request, "portal/editor.html", {"title": f"Информация · {project.title}", "form": form})


@login_required
@require_http_methods(["GET", "POST"])
def event_create(request, pk):
    require_writer(request.user)
    project = get_object_or_404(Project, pk=pk)
    form = GameEventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.project = project
        item.save()
        messages.success(request, "Событие добавлено в хронологию")
        return redirect(f"/information/?project={project.pk}#events")
    return render(request, "portal/editor.html", {"title": f"Новое событие · {project.title}", "form": form})


@login_required
@require_http_methods(["GET", "POST"])
def event_edit(request, pk):
    require_writer(request.user)
    event = get_object_or_404(GameEvent, pk=pk)
    form = GameEventForm(request.POST or None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Событие обновлено")
        return redirect(f"/information/?project={event.project_id}#events")
    return render(request, "portal/editor.html", {"title": f"Событие · {event.title}", "form": form})


@login_required
@require_http_methods(["GET", "POST"])
def character_create(request, pk):
    require_writer(request.user)
    project = get_object_or_404(Project, pk=pk)
    form = GameCharacterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        character = form.save(commit=False)
        character.project = project
        character.save()
        messages.success(request, "Персонаж добавлен")
        return redirect(f"/information/?project={project.pk}#characters")
    return render(request, "portal/editor.html", {"title": f"Новый персонаж · {project.title}", "form": form})


@login_required
@require_http_methods(["GET", "POST"])
def character_edit(request, pk):
    require_writer(request.user)
    character = get_object_or_404(GameCharacter, pk=pk)
    form = GameCharacterForm(request.POST or None, instance=character)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Персонаж обновлён")
        return redirect(f"/information/?project={character.project_id}#characters")
    return render(request, "portal/editor.html", {"title": f"Персонаж · {character.name}", "form": form})
