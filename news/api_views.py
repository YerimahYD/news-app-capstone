"""news/api_views.py — RESTful API views for the news application."""

import json
import requests

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.utils import timezone

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ApprovedArticleLog, Article, Newsletter,
    ROLE_EDITOR, ROLE_JOURNALIST, ROLE_READER,
)
from .serializers import (
    ApprovedArticleLogSerializer, ArticleSerializer, NewsletterSerializer,
)

User = get_user_model()


class CustomObtainAuthToken(ObtainAuthToken):
    """Return a token and basic user info on successful login."""

    def post(self, request, *args, **kwargs):
        """Handle POST request and return auth token with user details."""
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'role': user.role,
        })


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_article_list(request):
    """GET all approved articles or POST a new one (journalists only)."""
    if request.method == 'GET':
        articles = Article.objects.filter(approved=True)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    if request.user.role != ROLE_JOURNALIST:
        return Response(
            {'error': 'Only journalists can create articles.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ArticleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_article_detail(request, pk):
    """GET, PUT, or DELETE a single article."""
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response(
            {'error': 'Article not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    user = request.user
    if not (article.author == user or user.role == ROLE_EDITOR):
        return Response(
            {'error': 'Permission denied.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'PUT':
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    article.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_subscribed_articles(request):
    """Return approved articles from the user's subscribed sources."""
    from django.db.models import Q

    user = request.user

    if user.role == ROLE_READER:
        sub_publishers = user.subscribed_publishers.all()
        sub_journalists = user.subscribed_journalists.all()
        articles = Article.objects.filter(approved=True).filter(
            Q(publisher__in=sub_publishers) | Q(author__in=sub_journalists)
        ).distinct()
    elif user.role == ROLE_JOURNALIST:
        articles = Article.objects.filter(approved=True, author=user)
    else:
        articles = Article.objects.filter(approved=True)

    serializer = ArticleSerializer(articles, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_approved_log(request):
    """GET or POST to the approved article log."""
    if request.method == 'GET':
        logs = ApprovedArticleLog.objects.all()
        serializer = ApprovedArticleLogSerializer(logs, many=True)
        return Response(serializer.data)

    serializer = ApprovedArticleLogSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_newsletter_list(request):
    """GET all newsletters or POST a new one (journalists only)."""
    if request.method == 'GET':
        newsletters = Newsletter.objects.all()
        serializer = NewsletterSerializer(newsletters, many=True)
        return Response(serializer.data)

    if request.user.role != ROLE_JOURNALIST:
        return Response(
            {'error': 'Only journalists can create newsletters.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = NewsletterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def notify_subscribers(article, request=None):
    """Email subscribers and POST to /api/approved/ on article approval."""
    subscribers = _get_subscribers(article)
    _send_approval_emails(article, subscribers)
    _post_to_approved_log(article, request)


def _get_subscribers(article):
    """Return all users subscribed to the article's author or publisher."""
    by_journalist = User.objects.filter(
        subscribed_journalists=article.author
    )
    if article.publisher:
        by_publisher = User.objects.filter(
            subscribed_publishers=article.publisher
        )
    else:
        by_publisher = User.objects.none()
    return (by_journalist | by_publisher).distinct()


def _send_approval_emails(article, subscribers):
    """Send approval notification emails to all subscribers."""
    for subscriber in subscribers:
        if not subscriber.email:
            continue
        body = (
            f"Hi {subscriber.username},\n\n"
            f"A new article has been published:\n\n"
            f"Title: {article.title}\n"
            f"Author: {article.author.username}\n\n"
            f"{article.content[:300]}...\n\n"
            f"Log in to read the full article."
        )
        EmailMessage(
            subject=f"New article: {article.title}",
            body=body,
            from_email="noreply@newsapp.example.com",
            to=[subscriber.email],
        ).send()


def _post_to_approved_log(article, request=None):
    """POST article data to /api/approved/ to log the approval."""
    payload = {
        'article': article.pk,
        'payload': json.dumps({
            'id': article.pk,
            'title': article.title,
            'author': article.author.username,
            'approved_at': article.approved_at.isoformat()
            if article.approved_at else None,
        }),
    }
    try:
        if request:
            base_url = request.build_absolute_uri('/api/approved/')
        else:
            base_url = 'http://127.0.0.1:8000/api/approved/'
        token = Token.objects.filter(user=article.approved_by).first()
        if token:
            requests.post(
                base_url,
                data=payload,
                headers={'Authorization': f'Token {token.key}'},
                timeout=5,
            )
    except Exception:
        pass
