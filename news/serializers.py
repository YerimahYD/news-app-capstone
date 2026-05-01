"""news/serializers.py — DRF serializers for the news application."""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Article, Newsletter, Publisher, ApprovedArticleLog

User = get_user_model()


class PublisherSerializer(serializers.ModelSerializer):
    """Serialise Publisher objects."""

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class UserSerializer(serializers.ModelSerializer):
    """Serialise CustomUser objects."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'publisher']
        read_only_fields = ['id', 'role']


class ArticleSerializer(serializers.ModelSerializer):
    """Serialise Article objects."""

    author_username = serializers.CharField(
        source='author.username', read_only=True
    )
    publisher_name = serializers.CharField(
        source='publisher.name', read_only=True, allow_null=True
    )

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'author', 'author_username',
            'publisher', 'publisher_name', 'created_at',
            'approved', 'approved_by', 'approved_at',
        ]
        read_only_fields = [
            'author', 'approved', 'approved_by', 'approved_at', 'created_at'
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialise Newsletter objects."""

    author_username = serializers.CharField(
        source='author.username', read_only=True
    )

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'description', 'author', 'author_username',
            'articles', 'created_at',
        ]
        read_only_fields = ['author', 'created_at']


class ApprovedArticleLogSerializer(serializers.ModelSerializer):
    """Serialise ApprovedArticleLog entries."""

    class Meta:
        model = ApprovedArticleLog
        fields = ['id', 'article', 'logged_at', 'payload']
        read_only_fields = ['logged_at']
