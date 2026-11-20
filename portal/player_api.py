"""Authenticated editorial API for the GitHub Pages Nightwell Dev client."""
import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .access import can_write
from .api import error, payload, require_token
from .forms import PublicGamePageForm, PublicGameNewsForm
from .models import Project, PublicGamePage, PublicGameNews


def project_main():
    return get_object_or_404(Project, slug="main")


def page_data(page):
    return {
        name: getattr(page, name)
        for name in PublicGamePageForm.Meta.fields
    }


def news_data(item):
    return {
        "id": item.pk, "title": item.title, "summary": item.summary,
        "content": item.content, "is_published": item.is_published,
        "date": item.published_at.date().isoformat(),
    }


@csrf_exempt
@require_http_methods(["GET", "PUT"])
@require_token
def player_site(request):
    project = project_main()
    page, _ = PublicGamePage.objects.get_or_create(project=project, defaults={"title": "ASHFALL"})
    if request.method == "PUT":
        if not can_write(request.native_user):
            return error("Недостаточно прав", 403)
        try:
            data = payload(request)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return error("Неверный формат JSON")
        current = page_data(page)
        form = PublicGamePageForm({**current, **data}, instance=page)
        if not form.is_valid():
            return error("Проверь поля", 400, form.errors.get_json_data())
        page = form.save()
    return JsonResponse({
        "page": page_data(page),
        "news": [news_data(item) for item in PublicGameNews.objects.filter(project=project)[:100]],
        "can_write": can_write(request.native_user),
    }, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
@require_http_methods(["POST"])
@require_token
def create_news(request):
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    try:
        data = payload(request)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return error("Неверный формат JSON")
    form = PublicGameNewsForm(data)
    if not form.is_valid():
        return error("Проверь поля", 400, form.errors.get_json_data())
    item = form.save(commit=False)
    item.project = project_main()
    item.save()
    return JsonResponse({"item": news_data(item)}, status=201, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
@require_token
def update_news(request, pk):
    if not can_write(request.native_user):
        return error("Недостаточно прав", 403)
    item = get_object_or_404(PublicGameNews, pk=pk, project__slug="main")
    try:
        data = payload(request)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return error("Неверный формат JSON")
    defaults = {name: getattr(item, name) for name in PublicGameNewsForm.Meta.fields}
    form = PublicGameNewsForm({**defaults, **data}, instance=item)
    if not form.is_valid():
        return error("Проверь поля", 400, form.errors.get_json_data())
    form.save()
    return JsonResponse({"item": news_data(item)}, json_dumps_params={"ensure_ascii": False})
