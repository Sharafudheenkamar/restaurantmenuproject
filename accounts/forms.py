from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import User


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "role", "phone")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "email", "role", "phone")


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter username or email"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter password"})
    )


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Username or Email"}),
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        if username and "@" in username:
            user_model = get_user_model()
            user = user_model.objects.filter(email__iexact=username).first()
            if user:
                self.cleaned_data["username"] = user.get_username()
        return super().clean()


class ForgotPasswordEmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your registered email",
                "autocomplete": "email",
            }
        )
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        user_model = get_user_model()
        if not user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("No account found with this email address.")
        return email
