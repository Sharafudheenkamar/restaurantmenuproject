from django.urls import path
from .views import MakePaymentView

urlpatterns = [
    path('pay/<int:order_id>/', MakePaymentView.as_view(), name='make-payment'),
]
