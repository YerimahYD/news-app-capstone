"""news/views.py — Web UI views for the news application.

Fixes applied
-------------
- Publisher registration: publishers can now register via /publishers/register/
- Unique email: CustomUserCreationForm validates email uniqueness
- Newsletter guardrail: readers only see approved articles in newsletters
- Subscribe/unsubscribe: readers can follow publishers and journalists
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .api_views import notify_subscribers
from .forms import (
    ArticleForm, CustomUserCreationForm, NewsletterForm,
    PublisherRegistrationForm,
)
from .models import (
    Article, CustomUser, Newsletter, Publisher,
    ROLE_EDITOR, ROLE_JOURNALIST, ROLE_READER,
)


# ---------------------------------------------------------------------------
# Group setup helper
# ---------------------------------------------------------------------------

def _ensure_groups():
    """Create Reader, Journalist, and Editor groups with permissions."""
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission

    reader_group, _ = Group.objects.get_or_create(name='Readers')
    journalist_group, _ = Group.objects.get_or_create(name='Journalists')
    editor_group, _ = Group.objects.get_or_create(name='Editors')

    article_ct = ContentType.objects.get_for_model(Article)
    newsletter_ct = ContentType.objects.get_for_model(Newsletter)

    for codename in ['view_article', 'view_newsletter']:
        ct = article_ct if 'article' in codename else newsletter_ct
        try:
            perm = Permission.objects.get(codename=codename, content_type=ct)
            reader_group.permissions.add(perm)
        except Permission.DoesNotExist:
            pass

    for codename in [
        'view_article', 'change_article', 'delete_article',
        'view_newsletter', 'change_newsletter', 'delete_newsletter',
    ]:
        ct = article_ct if 'article' in codename else newsletter_ct
        try:
            perm = Permission.objects.get(codename=codename, content_type=ct)
            editor_group.permissions.add(perm)
        except Permission.DoesNotExist:
            pass

    for codename in [
        'add_article', 'view_article', 'change_article', 'delete_article',
        'add_newsletter', 'view_newsletter', 'change_newsletter',
        'delete_newsletter',
    ]:
        ct = article_ct if 'article' in codename else newsletter_ct
        try:
            perm = Permission.objects.get(codename=codename, content_type=ct)
            journalist_group.permissions.add(perm)
        except Permission.DoesNotExist:
            pass

    return reader_group, journalist_group, editor_group


# ---------------------------------------------------------------------------
# Publisher registration (Fix 2)
# ---------------------------------------------------------------------------

def register_publisher(request):
    """Register a new publisher (publication).

    Publishers register separately. Once registered, journalists and
    editors can select the publisher when creating their accounts.

    GET  /publishers/register/ — show registration form
    POST /publishers/register/ — validate and save publisher
    """
    if request.method == 'POST':
        form = PublisherRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Publisher registered successfully! '
                'Journalists and editors can now select your publication '
                'when they register.'
            )
            return redirect('news:login')
    else:
        form = PublisherRegistrationForm()

    return render(request, 'news/register_publisher.html', {'form': form})


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def register(request):
    """Register a new user (reader, journalist, or editor).

    Journalists and editors can select a publisher during registration.
    Email uniqueness is enforced by the form's clean_email() method.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            reader_group, journalist_group, editor_group = _ensure_groups()

            if user.role == ROLE_READER:
                user.groups.add(reader_group)
            elif user.role == ROLE_JOURNALIST:
                user.groups.add(journalist_group)
            elif user.role == ROLE_EDITOR:
                user.groups.add(editor_group)

            login(request, user)
            return redirect('news:home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'news/register.html', {'form': form})


def login_view(request):
    """Log an existing user in."""
    if request.user.is_authenticated:
        return redirect('news:home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('news:home')
        error = 'Invalid username or password.'

    return render(request, 'news/login.html', {'error': error})


def logout_view(request):
    """Log the current user out."""
    logout(request)
    return redirect('news:login')


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@login_required
def home(request):
    """Landing page — shows approved articles."""
    articles = Article.objects.filter(approved=True).select_related(
        'author', 'publisher'
    )
    return render(request, 'news/home.html', {
        'articles': articles,
        'user': request.user,
    })


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

@login_required
def article_list(request):
    """List all approved articles."""
    articles = Article.objects.filter(approved=True).select_related(
        'author', 'publisher'
    )
    return render(request, 'news/article_list.html', {'articles': articles})


@login_required
def article_detail(request, pk):
    """View a single approved article."""
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'news/article_detail.html', {'article': article})


@login_required
def article_create(request):
    """Journalists only: submit a new article."""
    if not request.user.is_journalist():
        messages.error(request, 'Only journalists can create articles.')
        return redirect('news:home')

    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, 'Article submitted for review.')
            return redirect('news:article_list')
    else:
        form = ArticleForm()

    return render(request, 'news/article_form.html',
                  {'form': form, 'action': 'Submit'})


@login_required
def article_edit(request, pk):
    """Journalists (own article) or editors: edit an article."""
    article = get_object_or_404(Article, pk=pk)
    user = request.user

    if not (user.is_editor() or article.author == user):
        messages.error(request, 'Permission denied.')
        return redirect('news:article_list')

    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated.')
            return redirect('news:article_detail', pk=pk)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'news/article_form.html',
                  {'form': form, 'article': article, 'action': 'Edit'})


@login_required
def article_delete(request, pk):
    """Editors or owning journalist: delete an article."""
    article = get_object_or_404(Article, pk=pk)
    user = request.user

    if not (user.is_editor() or article.author == user):
        messages.error(request, 'Permission denied.')
        return redirect('news:article_list')

    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted.')
        return redirect('news:article_list')

    return render(request, 'news/article_confirm_delete.html',
                  {'article': article})


@login_required
def article_approve(request, pk):
    """Editors only: approve an article and notify subscribers.

    On approval (Option 2 — without signals):
    1. Marks article as approved with timestamp and approving editor.
    2. Emails all subscribers of the journalist or publisher.
    3. POSTs to /api/approved/ to log the approval.
    """
    if not request.user.is_editor():
        messages.error(request, 'Only editors can approve articles.')
        return redirect('news:pending_articles')

    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        article.approved = True
        article.approved_by = request.user
        article.approved_at = timezone.now()
        article.save()

        notify_subscribers(article, request)

        messages.success(
            request,
            f'"{article.title}" approved and subscribers notified.'
        )
        return redirect('news:pending_articles')

    return render(request, 'news/article_approve.html', {'article': article})


@login_required
def pending_articles(request):
    """Editors only: list articles awaiting approval."""
    if not request.user.is_editor():
        messages.error(request, 'Only editors can access this page.')
        return redirect('news:home')

    articles = Article.objects.filter(approved=False).select_related(
        'author', 'publisher'
    )
    return render(request, 'news/pending_articles.html',
                  {'articles': articles})


# ---------------------------------------------------------------------------
# Newsletters
# ---------------------------------------------------------------------------

@login_required
def newsletter_list(request):
    """List all newsletters."""
    newsletters = Newsletter.objects.all().select_related('author')
    return render(request, 'news/newsletter_list.html',
                  {'newsletters': newsletters})


@login_required
def newsletter_detail(request, pk):
    """View a single newsletter.

    Fix: readers only see approved articles within the newsletter.
    This prevents readers from accessing unapproved articles via newsletters.
    Editors and journalists see all articles.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    user = request.user

    if user.is_reader():
        articles = newsletter.articles.filter(approved=True)
    else:
        articles = newsletter.articles.all()

    return render(request, 'news/newsletter_detail.html', {
        'newsletter': newsletter,
        'articles': articles,
    })


@login_required
def newsletter_create(request):
    """Journalists and editors only: create a newsletter."""
    if not (request.user.is_journalist() or request.user.is_editor()):
        messages.error(
            request, 'Only journalists and editors can create newsletters.'
        )
        return redirect('news:newsletter_list')

    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(request, 'Newsletter created.')
            return redirect('news:newsletter_list')
    else:
        form = NewsletterForm()

    return render(request, 'news/newsletter_form.html',
                  {'form': form, 'action': 'Create'})


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

@login_required
def publisher_list(request):
    """List all publishers with subscribe/unsubscribe buttons for readers."""
    publishers = Publisher.objects.all()
    subscribed_ids = []

    if request.user.is_reader():
        subscribed_ids = list(
            request.user.subscribed_publishers.values_list('id', flat=True)
        )

    return render(request, 'news/publisher_list.html', {
        'publishers': publishers,
        'subscribed_ids': subscribed_ids,
    })


@login_required
def subscribe_publisher(request, pk):
    """Readers only: subscribe to a publisher."""
    if not request.user.is_reader():
        messages.error(request, 'Only readers can subscribe to publishers.')
        return redirect('news:publisher_list')

    publisher = get_object_or_404(Publisher, pk=pk)

    if request.method == 'POST':
        request.user.subscribed_publishers.add(publisher)
        messages.success(request, f'Subscribed to {publisher.name}.')

    return redirect('news:publisher_list')


@login_required
def unsubscribe_publisher(request, pk):
    """Readers only: unsubscribe from a publisher."""
    if not request.user.is_reader():
        messages.error(request, 'Only readers can manage subscriptions.')
        return redirect('news:publisher_list')

    publisher = get_object_or_404(Publisher, pk=pk)

    if request.method == 'POST':
        request.user.subscribed_publishers.remove(publisher)
        messages.success(request, f'Unsubscribed from {publisher.name}.')

    return redirect('news:publisher_list')


@login_required
def journalist_list(request):
    """List all journalists with subscribe/unsubscribe buttons for readers."""
    journalists = CustomUser.objects.filter(role=ROLE_JOURNALIST)
    subscribed_ids = []

    if request.user.is_reader():
        subscribed_ids = list(
            request.user.subscribed_journalists.values_list('id', flat=True)
        )

    return render(request, 'news/journalist_list.html', {
        'journalists': journalists,
        'subscribed_ids': subscribed_ids,
    })


@login_required
def subscribe_journalist(request, pk):
    """Readers only: subscribe to a journalist."""
    if not request.user.is_reader():
        messages.error(request, 'Only readers can subscribe to journalists.')
        return redirect('news:journalist_list')

    journalist = get_object_or_404(CustomUser, pk=pk, role=ROLE_JOURNALIST)

    if request.method == 'POST':
        request.user.subscribed_journalists.add(journalist)
        messages.success(request, f'Subscribed to {journalist.username}.')

    return redirect('news:journalist_list')


@login_required
def unsubscribe_journalist(request, pk):
    """Readers only: unsubscribe from a journalist."""
    if not request.user.is_reader():
        messages.error(request, 'Only readers can manage subscriptions.')
        return redirect('news:journalist_list')

    journalist = get_object_or_404(CustomUser, pk=pk, role=ROLE_JOURNALIST)

    if request.method == 'POST':
        request.user.subscribed_journalists.remove(journalist)
        messages.success(request, f'Unsubscribed from {journalist.username}.')

    return redirect('news:journalist_list')
