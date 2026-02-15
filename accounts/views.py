from django.shortcuts import redirect
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

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "customer":
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        user = self.request.user
        print(user.role)
                # get next from POST first (important), then GET
        next_url = self.request.POST.get("next") or self.request.GET.get("next")

        # ✅ CUSTOMER → go to menu WITH table id
        if user.role == "customer":
            if next_url:
                return next_url
            return reverse_lazy("menu:menu-list")

        if user.role == "admin":
            return reverse_lazy("administrator:admin-dashboard")

        elif user.role == "kitchen":
            return reverse_lazy("kitchen-orders")
        
        elif user.role == "customer":
            return reverse_lazy("menu:menu-list")

        
    

        else:
            return reverse_lazy("login")

class ProfileView(TemplateView):
    template_name = 'user/profile.html'
