from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import SignupForm,LoginForm

class SignupView(CreateView):
    form_class = SignupForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    
    def get_success_url(self):
        user = self.request.user
        print(user)

        if user.role == "admin":
            return reverse_lazy("administrator:admin-dashboard")

        elif user.role == "kitchen":
            return reverse_lazy("kitchen-orders")

        else:
            return reverse_lazy("menu-list")

class ProfileView(TemplateView):
    template_name = 'user/profile.html'
