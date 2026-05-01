"""news/permissions.py — Custom DRF permission classes."""

from rest_framework.permissions import BasePermission
from .models import ROLE_EDITOR, ROLE_JOURNALIST, ROLE_READER


class IsReader(BasePermission):
    """Allow access only to users with the Reader role."""

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role == ROLE_READER)


class IsJournalist(BasePermission):
    """Allow access only to users with the Journalist role."""

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role == ROLE_JOURNALIST)


class IsEditor(BasePermission):
    """Allow access only to users with the Editor role."""

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role == ROLE_EDITOR)


class IsJournalistOrEditor(BasePermission):
    """Allow access to Journalists and Editors."""

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in (ROLE_JOURNALIST, ROLE_EDITOR))
