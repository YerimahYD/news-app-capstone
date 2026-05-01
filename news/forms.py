"""news/forms.py — Forms for the news application."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Article, CustomUser, Newsletter, Publisher, ROLE_CHOICES


class CustomUserCreationForm(UserCreationForm):
    """Registration form for readers, journalists and editors.

    Fix: validates that the email address is unique — raises a
    ValidationError if another user has already registered with it.
    """

    email = forms.EmailField(
        required=True,
        help_text='Required. Must be unique.',
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    publisher = forms.ModelChoiceField(
        queryset=Publisher.objects.all(),
        required=False,
        empty_label='— Independent (no publisher) —',
        help_text='Select your publisher if you are a journalist or editor.',
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'publisher',
                  'password1', 'password2']

    def clean_email(self):
        """Validate that the email address is not already registered."""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                'A user with this email address already exists. '
                'Please use a different email or log in.'
            )
        return email

    def save(self, commit=True):
        """Save the user with the selected role and publisher."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.publisher = self.cleaned_data.get('publisher')
        if commit:
            user.save()
        return user


class PublisherRegistrationForm(forms.ModelForm):
    """Form for registering a new publisher (publication).

    Publishers register separately from individual users.
    Once registered, editors and journalists can select the publisher
    when they create their own accounts.
    """

    class Meta:
        model = Publisher
        fields = ['name', 'description', 'contact_email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Publication name…',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description of the publication…',
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@publication.com',
            }),
        }

    def clean_contact_email(self):
        """Validate that the contact email is not already registered."""
        email = self.cleaned_data.get('contact_email')
        if Publisher.objects.filter(contact_email=email).exists():
            raise ValidationError(
                'A publisher with this email address already exists.'
            )
        return email


class ArticleForm(forms.ModelForm):
    """Form for creating and editing articles."""

    class Meta:
        model = Article
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Article headline…',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Write your article here…',
            }),
            'publisher': forms.Select(attrs={'class': 'form-control'}),
        }


class NewsletterForm(forms.ModelForm):
    """Form for creating and editing newsletters."""

    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'articles']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
            'articles': forms.CheckboxSelectMultiple(),
        }
