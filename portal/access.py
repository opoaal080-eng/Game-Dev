from django.core.exceptions import PermissionDenied
from .models import Profile


def role_of(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return Profile.Role.ADMIN
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile.role


def can_write(user):
    return role_of(user) in (Profile.Role.DEVELOPER, Profile.Role.ADMIN)


def is_admin(user):
    return role_of(user) == Profile.Role.ADMIN


def require_writer(user):
    if not can_write(user):
        raise PermissionDenied("Недостаточно прав")


def require_owner_or_admin(user, owner_id):
    require_writer(user)
    if owner_id != user.pk and not is_admin(user):
        raise PermissionDenied("Редактировать может только автор или администратор")
