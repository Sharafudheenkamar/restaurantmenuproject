from django.views.generic import ListView
from .models import MenuItem

class TodayMenuView(ListView):
    model = MenuItem
    template_name = 'user/menu.html'
    context_object_name = 'items'
    def get(self, request, *args, **kwargs):
        table = request.GET.get("table")
        if table:
            request.session["table"] = table
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return MenuItem.objects.filter(is_available=True)
