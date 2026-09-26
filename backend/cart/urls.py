from django.urls import path

from . import views

urlpatterns = [
    path(
        'cart/menu-items',
        views.CartView.as_view()
    ),
    path(
        'cart/menu-items/<int:menuitem_id>',
        views.CartItemView.as_view()
    ),
]
