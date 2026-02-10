from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth & Accounts
    path('accounts/', include('accounts.urls')),

    # Menu & QR
    path('', include('menu.urls')),

    # Cart
    path('cart/', include('cart.urls')),

    # Orders
    path('orders/', include('orders.urls')),

    # Payments
    path('payments/', include('payments.urls')),

    # Feedback
    path('feedback/', include('feedback.urls')),

    # Web Push Notifications
    path('webpush/', include('webpush.urls')),
    path('administrator/', include('administrator.urls')),

]
