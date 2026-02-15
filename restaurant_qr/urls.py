from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth & Accounts
    path('', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Menu & QR
    path('menu/', include(('menu.urls','menu'),namespace='menu')),

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

    # Administrator
    path('administrator/', include(('administrator.urls','administrator'),namespace='administrator')),

    # Kitchen
    # path('')

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)