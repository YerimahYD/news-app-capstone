"""news/admin.py — Register all models with Django admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    ApprovedArticleLog, Article, CustomUser, Newsletter, Publisher
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser."""

    list_display = ['username', 'email', 'role', 'publisher']
    list_filter = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Subscriptions', {
            'fields': (
                'role', 'publisher',
                'subscribed_publishers', 'subscribed_journalists',
            )
        }),
    )


admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)
admin.site.register(ApprovedArticleLog)
