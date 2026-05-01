"""news/urls.py — URL patterns for the news application."""

from django.urls import path
from . import views, api_views

app_name = 'news'

urlpatterns = [
    # -----------------------------------------------------------------------
    # Web UI — Auth
    # -----------------------------------------------------------------------
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Publisher registration (Fix 2)
    path('publishers/register/', views.register_publisher,
         name='register_publisher'),

    # -----------------------------------------------------------------------
    # Web UI — Articles
    # -----------------------------------------------------------------------
    path('articles/', views.article_list, name='article_list'),
    path('articles/new/', views.article_create, name='article_create'),
    path('articles/pending/', views.pending_articles, name='pending_articles'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/<int:pk>/edit/', views.article_edit, name='article_edit'),
    path('articles/<int:pk>/delete/', views.article_delete,
         name='article_delete'),
    path('articles/<int:pk>/approve/', views.article_approve,
         name='article_approve'),

    # -----------------------------------------------------------------------
    # Web UI — Newsletters
    # -----------------------------------------------------------------------
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/new/', views.newsletter_create,
         name='newsletter_create'),
    path('newsletters/<int:pk>/', views.newsletter_detail,
         name='newsletter_detail'),

    # -----------------------------------------------------------------------
    # Web UI — Subscriptions
    # -----------------------------------------------------------------------
    path('publishers/', views.publisher_list, name='publisher_list'),
    path('publishers/<int:pk>/subscribe/', views.subscribe_publisher,
         name='subscribe_publisher'),
    path('publishers/<int:pk>/unsubscribe/', views.unsubscribe_publisher,
         name='unsubscribe_publisher'),
    path('journalists/', views.journalist_list, name='journalist_list'),
    path('journalists/<int:pk>/subscribe/', views.subscribe_journalist,
         name='subscribe_journalist'),
    path('journalists/<int:pk>/unsubscribe/', views.unsubscribe_journalist,
         name='unsubscribe_journalist'),

    # -----------------------------------------------------------------------
    # REST API
    # -----------------------------------------------------------------------
    path('api/token/', api_views.CustomObtainAuthToken.as_view(),
         name='api_token'),
    path('api/articles/', api_views.api_article_list,
         name='api_article_list'),
    path('api/articles/subscribed/', api_views.api_subscribed_articles,
         name='api_subscribed_articles'),
    path('api/articles/<int:pk>/', api_views.api_article_detail,
         name='api_article_detail'),
    path('api/approved/', api_views.api_approved_log,
         name='api_approved_log'),
    path('api/newsletters/', api_views.api_newsletter_list,
         name='api_newsletter_list'),
]
