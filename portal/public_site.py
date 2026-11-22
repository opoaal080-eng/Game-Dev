"""Public ASHFALL data is explicitly curated. Never expose private Dev models."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from .models import Project, PublicGamePage, PublicGameNews

PUBLIC_PROJECT_SLUG = "main"


def secure_link(value):
    value = (value or "").strip()
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
            return value
    except (ValueError, TypeError):
        pass
    return ""


def public_payload():
    """Returns ONLY intentionally public content, never internal descriptions or files."""
    project = Project.objects.filter(slug=PUBLIC_PROJECT_SLUG).first()
    page = PublicGamePage.objects.filter(project=project, is_published=True).first() if project else None
    if not page:
        return {
            "schema": 1, "published": False, "title": "ASHFALL",
            "eyebrow": "NIGHTWELL STUDIO · ИГРОВОЙ ПРОЕКТ", "tagline": "",
            "introduction": "", "story_teaser": "", "world_description": "",
            "feature_lines": [], "genre": "", "platforms": "",
            "development_status": "", "release_window": "", "hero_image_url": "",
            "trailer_url": "", "screenshots": [], "community_url": "",
            "telegram_url": "", "wishlist_url": "", "contact_email": "",
            "news": [], "updated_at": None,
        }
    screenshots = [secure_link(item) for item in page.screenshots.splitlines()]
    news = PublicGameNews.objects.filter(project=project, is_published=True).order_by("-published_at", "-id")[:12]
    return {
        "schema": 1,
        "published": True,
        "title": page.title or "ASHFALL",
        "eyebrow": page.eyebrow,
        "tagline": page.tagline,
        "introduction": page.introduction,
        "story_teaser": page.story_teaser,
        "world_description": page.world_description,
        "feature_lines": [v.strip() for v in page.feature_lines.splitlines() if v.strip()][:12],
        "genre": page.genre,
        "platforms": page.platforms,
        "development_status": page.development_status,
        "release_window": page.release_window,
        "hero_image_url": secure_link(page.hero_image_url),
        "trailer_url": secure_link(page.trailer_url),
        "screenshots": [v for v in screenshots if v][:16],
        "community_url": secure_link(page.community_url),
        "telegram_url": secure_link(page.telegram_url),
        "wishlist_url": secure_link(page.wishlist_url),
        "contact_email": page.contact_email,
        "news": [{
            "id": item.pk,
            "title": item.title,
            "summary": item.summary,
            "content": item.content,
            "date": item.published_at.date().isoformat(),
        } for item in news],
        "updated_at": page.updated_at.isoformat(),
    }


@require_GET
def public_data(request):
    response = JsonResponse(public_payload(), json_dumps_params={"ensure_ascii": False})
    response["Cache-Control"] = "public, max-age=60, s-maxage=60"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def public_shell(request):
    path = Path(settings.BASE_DIR) / "ashfall" / "index.html"
    if not path.exists():
        raise Http404("ASHFALL frontend unavailable")
    response = HttpResponse(path.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "public, max-age=120"
    return response


class AshfallCustomDomainMiddleware:
    """Route afl.nightwell.fun root to the public site, not private Dev login."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        if host == "afl.nightwell.fun":
            if request.path == "/":
                return public_shell(request)
            if request.path == "/data/public.json":
                return public_data(request)
        return self.get_response(request)
