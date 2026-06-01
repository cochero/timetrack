from rest_framework.permissions import BasePermission, SAFE_METHODS

# Roles that are allowed to see data beyond their own and to manage setup data.
MANAGER_ROLES = {
    "OWNER", "ADMIN", "PROJECT_HEAD", "PROJECT_MANAGER", "TEAM_LEADER"
}


class IsAuthenticatedInOrg(BasePermission):
    """User must be logged in AND belong to an organization."""
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.organization_id)


class IsManager(BasePermission):
    """User must hold a management role."""
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role in MANAGER_ROLES)


class IsManagerOrReadOnly(BasePermission):
    """Anyone logged in can read; only managers can create / change / delete."""
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if request.method in SAFE_METHODS:   # GET, HEAD, OPTIONS
            return True
        return u.role in MANAGER_ROLES
