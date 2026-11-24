"""JSON API for fully native Nightwell Dev clients.

Authentication is bearer-token only, independent of browser sessions and cookies.
Tokens are random, revocable, expire in 30 days and are stored as SHA-256 digests.
All mutation endpoints require an authenticated token and project-specific permissions.
"""
import hashlib
import json
import secrets
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .access import can_write, is_admin, role_of
from .forms import AssetForm, PostForm, TaskForm, GameInfoForm, GameEventForm, GameCharacterForm
from .models import AppSession, Asset, Post, Project, Task, GameInfo, GameEvent, GameCharacter


def error(message, status=400, errors=None):
    data = {"error": message}
    if errors:
        data["fields"] = errors
    return JsonResponse(data, status=status)


def payload(request):
    if request.content_type != "application/json":
        raise ValueError("Expected application/json")
    raw = request.body
    if len(raw) > 1024 * 1024:
        raise ValueError("JSON body is too large")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    return data


def require_token(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or len(auth) > 256:
            return error("Требуется вход в приложение", 401)
        token = auth[7:].strip()
        if not token:
            return error("Требуется вход в приложение", 401)
        digest = hashlib.sha256(token.encode()).hexdigest()
        session = AppSession.objects.select_related("user").filter(token_hash=digest, expires_at__gt=timezone.now(), user__is_active=True).first()
        if session is None:
            return error("Сессия истекла. Войдите снова", 401)
        request.native_user = session.user
        request.native_session = session
        if (timezone.now() - session.last_used_at).total_seconds() > 600:
            AppSession.objects.filter(pk=session.pk).update(last_used_at=timezone.now())
        return view(request, *args, **kwargs)
    return wrapper


def user_json(user):
    return {"id": user.pk, "username": user.username,
            "name": user.get_full_name() or user.username,
            "role": role_of(user), "can_write": can_write(user),
            "job_title": getattr(getattr(user, "dev_profile", None), "job_title", "")}


def project_json(project):
    return {"id": project.pk, "name": project.title,
            "slug": project.slug, "description": project.description}


def post_json(post):
    return {"id": post.pk, "project_id": post.project_id, "project": post.project.title,
            "title": post.title, "body": post.body, "kind": post.kind, "status": post.status,
            "content_mode": post.content_mode, "code_language": post.code_language,
            "pinned": post.pinned, "author": post.author.username,
            "author_id": post.author_id, "updated_at": post.updated_at.isoformat()}


def task_json(task):
    return {"id": task.pk, "project_id": task.project_id, "project": task.project.title,
            "title": task.title, "description": task.description,
            "status": task.status, "priority": task.priority,
            "assignee": task.assignee.username if task.assignee else None,
            "assignee_id": task.assignee_id, "created_by_id": task.created_by_id,
            "due_date": task.due_date.isoformat() if task.due_date else None}


def asset_json(asset):
    return {"id": asset.pk, "project_id": asset.project_id,
            "title": asset.title, "original_name": asset.original_name,
            "description": asset.description, "size": asset.size,
            "uploader": asset.uploaded_by.username,
            "download_path": f"/api/v1/files/{asset.pk}/download/"}


def info_json(item, project):
    keys = ("title", "genre", "tagline", "setting", "story", "gameplay", "themes",
            "universe", "platforms", "engine", "development_status", "audience", "notes")
    return {"project_id": project.pk, "project": project.title,
            **{name: getattr(item, name, "") if item else "" for name in keys}}


def event_json(item):
    keys = ("id", "project_id", "chapter", "title", "kind", "order",
            "timeline", "location", "participants", "summary", "description",
            "consequences", "spoiler")
    return {name: getattr(item, name) for name in keys}


def character_json(item):
    keys = ("id", "project_id", "name", "role", "faction", "bio", "motivation", "notes", "order")
    return {name: getattr(item, name) for name in keys}


def native_posts(user):
    qs = Post.objects.select_related("project", "author")
    if not can_write(user):
        qs = qs.filter(status="published")
    return qs


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        data = payload(request)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    device = str(data.get("device_name", ""))[:100]
    if len(username) > 150 or len(password) > 1024:
        return error("Неверный логин или пароль", 401)
    # Per-worker throttling. The deployment edge should also have rate limiting.
    key = "native-login:" + hashlib.sha256((request.META.get("REMOTE_ADDR", "") + ":" + username.lower()).encode()).hexdigest()
    count = cache.get(key, 0)
    if count >= 10:
        return error("Слишком много попыток. Повторите позже", 429)
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        cache.set(key, count + 1, timeout=900)
        return error("Неверный логин или пароль", 401)
    cache.delete(key)
    AppSession.objects.filter(expires_at__lt=timezone.now()).delete()
    token = secrets.token_urlsafe(48)
    expires = timezone.now() + timedelta(days=30)
    AppSession.objects.create(user=user, token_hash=hashlib.sha256(token.encode()).hexdigest(),
                              device_name=device, expires_at=expires)
    return JsonResponse({"token": token, "expires_at": expires.isoformat(), "user": user_json(user)})


@csrf_exempt
@require_http_methods(["POST"])
@require_token
def logout(request):
    AppSession.objects.filter(pk=request.native_session.pk).delete()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST"])
@require_token
def change_password(request):
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    old = data.get("old_password", "")
    new = data.get("new_password", "")
    user = request.native_user
    if not isinstance(old, str) or not isinstance(new, str) or not user.check_password(old):
        return error("Неверный текущий пароль", 400)
    try:
        validate_password(new, user=user)
    except ValidationError as exc:
        return error("Пароль не подходит", 400, {"new_password": exc.messages})
    user.set_password(new)
    user.save(update_fields=["password"])
    AppSession.objects.filter(user=user).delete()
    return JsonResponse({"ok": True, "login_required": True})


@require_http_methods(["GET"])
@require_token
def me(request):
    return JsonResponse({"user": user_json(request.native_user)})


@require_http_methods(["GET"])
@require_token
def dashboard(request):
    user = request.native_user
    posts = native_posts(user)
    tasks = Task.objects.select_related("project", "assignee")
    return JsonResponse({
        "counts": {"posts": posts.count(), "tasks": tasks.exclude(status="done").count(),
                   "files": Asset.objects.count(), "members": get_user_model().objects.filter(is_active=True).count()},
        "latest_posts": [post_json(p) for p in posts[:6]],
        "active_tasks": [task_json(t) for t in tasks.exclude(status="done")[:8]],
        "projects": [project_json(p) for p in Project.objects.all()[:30]],
    })


@require_http_methods(["GET"])
@require_token
def projects(request):
    return JsonResponse({"items": [project_json(p) for p in Project.objects.all()[:100]]})


@csrf_exempt
@require_http_methods(["GET", "POST"])
@require_token
def posts(request):
    if request.method == "GET":
        qs = native_posts(request.native_user)
        kind = request.GET.get("kind", "")
        if kind in Post.Kind.values:
            qs = qs.filter(kind=kind)
        p = request.GET.get("project", "")
        if p.isdigit():
            qs = qs.filter(project_id=int(p))
        return JsonResponse({"items": [post_json(item) for item in qs[:100]]})
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    form = PostForm(data)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    post = form.save(commit=False)
    post.author = request.native_user
    post.save()
    return JsonResponse({"item": post_json(Post.objects.select_related("project", "author").get(pk=post.pk))}, status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@require_token
def post_detail(request, pk):
    user = request.native_user
    if request.method == "GET":
        post = native_posts(user).filter(pk=pk).first()
        return JsonResponse({"item": post_json(post)}) if post else error("Публикация не найдена", 404)
    post = Post.objects.select_related("project", "author").filter(pk=pk).first()
    if not post:
        return error("Не найдено", 404)
    if not can_write(user) or not (is_admin(user) or post.author_id == user.pk):
        return error("Недостаточно прав", 403)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    form = PostForm(data, instance=post)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    form.save()
    return JsonResponse({"item": post_json(post)})


@csrf_exempt
@require_http_methods(["GET", "POST"])
@require_token
def tasks(request):
    if request.method == "GET":
        qs = Task.objects.select_related("project", "assignee", "created_by")
        p = request.GET.get("project", "")
        if p.isdigit():
            qs = qs.filter(project_id=int(p))
        return JsonResponse({"items": [task_json(t) for t in qs[:150]]})
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    form = TaskForm(data)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    item = form.save(commit=False)
    item.created_by = request.native_user
    item.save()
    return JsonResponse({"item": task_json(Task.objects.select_related("project", "assignee").get(pk=item.pk))}, status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@require_token
def task_detail(request, pk):
    task = Task.objects.select_related("project", "assignee").filter(pk=pk).first()
    if not task:
        return error("Не найдено", 404)
    if request.method == "GET":
        return JsonResponse({"item": task_json(task)})
    user = request.native_user
    if not can_write(user) or not (is_admin(user) or task.created_by_id == user.pk or task.assignee_id == user.pk):
        return error("Недостаточно прав", 403)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    form = TaskForm(data, instance=task)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    form.save()
    return JsonResponse({"item": task_json(task)})


@csrf_exempt
@require_http_methods(["GET", "POST"])
@require_token
def files(request):
    if request.method == "GET":
        qs = Asset.objects.select_related("project", "uploaded_by")
        p = request.GET.get("project", "")
        if p.isdigit():
            qs = qs.filter(project_id=int(p))
        return JsonResponse({"items": [asset_json(a) for a in qs[:150]]})
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    form = AssetForm(request.POST, request.FILES)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    item = form.save(commit=False)
    uploaded = form.cleaned_data["file"]
    item.original_name = uploaded.name[:255]
    item.size = uploaded.size
    item.uploaded_by = request.native_user
    item.save()
    return JsonResponse({"item": asset_json(item)}, status=201)


@require_http_methods(["GET"])
@require_token
def file_download(request, pk):
    asset = Asset.objects.filter(pk=pk).first()
    if not asset:
        return error("Файл не найден", 404)
    try:
        stream = asset.file.open("rb")
    except (OSError, FileNotFoundError):
        return error("Файл не найден", 404)
    return FileResponse(stream, as_attachment=True, filename=asset.download_name, content_type="application/octet-stream")


@require_http_methods(["GET"])
@require_token
def team(request):
    users = get_user_model().objects.filter(is_active=True).order_by("username")
    return JsonResponse({"items": [user_json(u) for u in users[:100]]})


@csrf_exempt
@require_http_methods(["GET", "PUT"])
@require_token
def information(request, pk):
    project = Project.objects.filter(pk=pk).first()
    if not project:
        return error("Проект не найден", 404)
    current = GameInfo.objects.filter(project=project).first()
    if request.method == "PUT":
        if not can_write(request.native_user):
            return error("Недостаточно прав", 403)
        try:
            data = payload(request)
        except (ValueError, json.JSONDecodeError):
            return error("Неверный формат запроса")
        if current is None:
            current = GameInfo(project=project)
        form = GameInfoForm(data, instance=current)
        if not form.is_valid():
            return error("Проверьте поля", 400, form.errors.get_json_data())
        current = form.save()
    return JsonResponse({
        "info": info_json(current, project),
        "events": [event_json(e) for e in GameEvent.objects.filter(project=project)],
        "characters": [character_json(c) for c in GameCharacter.objects.filter(project=project)],
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_token
def create_event(request, pk):
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    project = Project.objects.filter(pk=pk).first()
    if not project:
        return error("Проект не найден", 404)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    form = GameEventForm(data)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    item = form.save(commit=False)
    item.project = project
    item.save()
    return JsonResponse({"item": event_json(item)}, status=201)


@csrf_exempt
@require_http_methods(["PATCH"])
@require_token
def update_event(request, pk):
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    item = GameEvent.objects.filter(pk=pk).first()
    if not item:
        return error("Событие не найдено", 404)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    combined = {name: getattr(item, name) for name in GameEventForm.Meta.fields}
    form = GameEventForm({**combined, **data}, instance=item)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    form.save()
    return JsonResponse({"item": event_json(item)})


@csrf_exempt
@require_http_methods(["POST"])
@require_token
def create_character(request, pk):
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    project = Project.objects.filter(pk=pk).first()
    if not project:
        return error("Проект не найден", 404)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    form = GameCharacterForm(data)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    item = form.save(commit=False)
    item.project = project
    item.save()
    return JsonResponse({"item": character_json(item)}, status=201)


@csrf_exempt
@require_http_methods(["PATCH"])
@require_token
def update_character(request, pk):
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    item = GameCharacter.objects.filter(pk=pk).first()
    if not item:
        return error("Персонаж не найден", 404)
    try:
        data = payload(request)
    except (ValueError, json.JSONDecodeError):
        return error("Неверный формат запроса")
    combined = {name: getattr(item, name) for name in GameCharacterForm.Meta.fields}
    form = GameCharacterForm({**combined, **data}, instance=item)
    if not form.is_valid():
        return error("Проверьте поля", 400, form.errors.get_json_data())
    form.save()
    return JsonResponse({"item": character_json(item)})
