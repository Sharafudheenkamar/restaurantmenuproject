from django.urls import path
from .views import FeedbackCreateView

urlpatterns = [
    path('submit/<int:order_id>/', FeedbackCreateView.as_view(), name='feedback'),
]
