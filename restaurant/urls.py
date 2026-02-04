from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path(
        'groups/manager/users', 
        views.GroupViewSet.as_view({'get': 'list', 'post': 'create'})
    ),
    path(
        "groups/manager/users/<int:userId>",
        views.GroupViewSet.as_view({"delete": "destroy"}),
    ),
    
    path(
        'groups/delivery-crew/users', 
         views.DeliveryCrewViewSet.as_view({'get': 'list', 'post': 'create'})
    ),
    path(
        "groups/delivery-crew/users/<int:userId>",
        views.DeliveryCrewViewSet.as_view({"delete": "destroy"}),
    ),
    
    path('api-token-auth/', obtain_auth_token),
    # path("users/", include("djoser.urls")),
    
    path('categories/', views.CategoriesView.as_view()),
    
    path(
        'menu-items/', 
         views.MenuItemsView.as_view()
    ),
    
    path(
        'menu-items/<int:pk>', 
        views.SingleMenuItemView.as_view()
    ),
]