from django.urls import path
# from .views import TodayMenuView, menu_api
from .views import TodayMenuView

urlpatterns = [
    # QR Scan lands here
    path('', TodayMenuView.as_view(), name='menu-list'),
    path('table/<int:table_id>/', TodayMenuView.as_view(), name='table-menu'),

    # Offline / PWA API
    # path('menu/api/', menu_api, name='menu-api'),
]
