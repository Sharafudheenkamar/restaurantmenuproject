from django.urls import path

from .views import AddToCartView, CartPageView, ClearCartView, DummyCheckoutView, RemoveCartItemView

urlpatterns = [
    path('', CartPageView.as_view(), name="cart-page"),
    path('add/', AddToCartView.as_view(), name="cart-add"),
    path('remove/<int:pk>/', RemoveCartItemView.as_view(), name="cart-remove"),
    path('clear/', ClearCartView.as_view(), name="cart-clear"),
    path('checkout/', DummyCheckoutView.as_view(), name="cart-checkout"),
]
