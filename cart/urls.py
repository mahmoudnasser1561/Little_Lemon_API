from django.urls import path

from . import views

urlpatterns = [
    path(
        'cart/menu-items',
        views.CartView.as_view()
    ),
]
