from django.views.generic import ListView
from .models import MenuItem

class TodayMenuView(ListView):
    model = MenuItem
    template_name = 'user/menu.html'
    context_object_name = 'items'

    def get_queryset(self):
        return MenuItem.objects.filter(is_available=True)
