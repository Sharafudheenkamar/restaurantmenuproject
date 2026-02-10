from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import SignupForm

class SignupView(CreateView):
    form_class = SignupForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'

class ProfileView(TemplateView):
    template_name = 'user/profile.html'
