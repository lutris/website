from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission to allow only admins to make changes."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff is True
