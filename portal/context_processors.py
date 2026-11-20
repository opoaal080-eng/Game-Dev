from .access import can_write, is_admin, role_of


def workspace(request):
    return {
        "can_write": can_write(request.user),
        "is_workspace_admin": is_admin(request.user),
        "workspace_role": role_of(request.user),
    }
