"""news/models.py — Data models for the news application.

Models
------
CustomUser  — extends AbstractUser with role-based fields and unique email
Publisher   — a publication that employs editors and journalists
Article     — a news article written by a journalist
Newsletter  — a curated collection of articles
ApprovedArticleLog — logs approved articles via /api/approved/
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------

ROLE_READER = 'reader'
ROLE_JOURNALIST = 'journalist'
ROLE_EDITOR = 'editor'

ROLE_CHOICES = [
    (ROLE_READER, 'Reader'),
    (ROLE_JOURNALIST, 'Journalist'),
    (ROLE_EDITOR, 'Editor'),
]


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

class Publisher(models.Model):
    """A publication that can have multiple editors and journalists.

    Publishers can register independently and then approve editors
    and journalists to work on their behalf.

    Attributes:
        name (str): Unique name of the publication.
        description (str): Short description of the publication.
        contact_email (str): Contact email for the publisher.
        created_at (datetime): When the publisher was registered.
    """

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Custom User
# ---------------------------------------------------------------------------

class CustomUser(AbstractUser):
    """Extends the built-in User with a role and role-specific fields.

    Fix: email is now unique=True to prevent multiple users registering
    with the same email address.

    Attributes:
        role (str): The user's role — reader, journalist, or editor.
        publisher (FK): The publisher this journalist/editor works for.
        subscribed_publishers (M2M): Publishers the reader subscribes to.
        subscribed_journalists (M2M): Journalists the reader subscribes to.
    """

    # Fix: unique email to prevent duplicate registrations
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_READER,
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
    )

    subscribed_publishers = models.ManyToManyField(
        Publisher,
        blank=True,
        related_name='subscribers',
    )

    subscribed_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='followers',
        limit_choices_to={'role': ROLE_JOURNALIST},
    )

    def is_reader(self):
        """Return True if this user has the Reader role."""
        return self.role == ROLE_READER

    def is_journalist(self):
        """Return True if this user has the Journalist role."""
        return self.role == ROLE_JOURNALIST

    def is_editor(self):
        """Return True if this user has the Editor role."""
        return self.role == ROLE_EDITOR

    def __str__(self):
        return f"{self.username} ({self.role})"


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------

class Article(models.Model):
    """A news article submitted by a journalist.

    Attributes:
        title (str): Headline of the article.
        content (str): Full body text.
        author (FK): The journalist who wrote the article.
        publisher (FK): Optional publisher association.
        created_at (datetime): Submission timestamp.
        approved (bool): Whether an editor has approved the article.
        approved_by (FK): The editor who approved it.
        approved_at (datetime): When it was approved.
    """

    title = models.CharField(max_length=300)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='articles',
        limit_choices_to={'role': ROLE_JOURNALIST},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_articles',
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = 'approved' if self.approved else 'pending'
        return f"{self.title} — {self.author.username} [{status}]"


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class Newsletter(models.Model):
    """A curated collection of articles created by a journalist.

    Attributes:
        title (str): Newsletter title.
        description (str): Brief description.
        author (FK): Journalist who created the newsletter.
        articles (M2M): Articles included in this newsletter.
        created_at (datetime): Creation timestamp.
    """

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='newsletters',
        limit_choices_to={'role': ROLE_JOURNALIST},
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name='newsletters',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author.username}"


# ---------------------------------------------------------------------------
# ApprovedArticleLog
# ---------------------------------------------------------------------------

class ApprovedArticleLog(models.Model):
    """Logs every article approved via the /api/approved/ endpoint.

    Attributes:
        article (FK): The approved article.
        logged_at (datetime): When the log entry was created.
        payload (str): JSON snapshot of the article data at approval time.
    """

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='approval_logs',
    )
    logged_at = models.DateTimeField(auto_now_add=True)
    payload = models.TextField(blank=True)

    def __str__(self):
        return f"Log: {self.article.title} at {self.logged_at}"
