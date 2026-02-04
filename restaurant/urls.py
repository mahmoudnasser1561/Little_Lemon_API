from django.urls import path
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
]