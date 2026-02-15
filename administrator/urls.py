from django.urls import path
from .views import *

urlpatterns = [
    path("", AdminDashboardView.as_view(), name="admin-dashboard"),

    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/add/", CategoryCreateView.as_view(), name="category-add"),
    path("categories/edit/<int:pk>/", CategoryUpdateView.as_view(), name="category-edit"),
    path("categories/delete/<int:pk>/", CategoryDeleteView.as_view(), name="category-delete"),


    path("menu/", MenuManageView.as_view(), name="admin-menu"),
    path("menu/add/", MenuCreateView.as_view(), name="admin-menu-add"),
    path("menu/edit/<int:pk>/", MenuUpdateView.as_view(), name="admin-menu-edit"),
    path("menu/delete/<int:pk>/", MenuDeleteView.as_view(), name="admin-menu-delete"),

    path("orders/", OrdersDashboardView.as_view(), name="admin-orders"),
    path("payments/", PaymentsDashboardView.as_view(), name="admin-payments"),
    path("staff/", StaffListView.as_view(), name="admin-staff"),
    path("staff/add/", StaffCreateView.as_view(), name="add-staff"),
    path("staff/edit/<int:pk>/", StaffUpdateView.as_view(), name="edit-staff"),
    path("staff/delete/<int:pk>/", StaffDeleteView.as_view(), name="delete-staff"),

    path("qr/<int:table_id>/", GenerateQRView.as_view(), name="generate-qr"),

    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),

    path("tables/", AdminTableListView.as_view(), name="admin-tables"),
    path("tables/add/", AddTableView.as_view(), name="add-table"),
    path("tables/delete/<int:pk>/", DeleteTableView.as_view(), name="delete-table"),
    path("tables/qr/<int:pk>/", GenerateQRView.as_view(), name="generate-qr"),

]
