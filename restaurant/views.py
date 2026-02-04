from rest_framework import generics, status, viewsets, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsManager
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer


# Manager Group Management
class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    
    # GET /api/groups/manager/users
    def list(self, request):
        users = User.objects.filter(groups__name='Manager')
        return Response([user.username for user in users])

    # POST /api/groups/manager/users
    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.add(user)
        return Response(status=status.HTTP_201_CREATED)

    # DELETE /api/groups/manager/users/{userId}
    def destroy(self, request, userId=None):
        user = get_object_or_404(User, id=userId)
        manager_group = Group.objects.get(name="Manager")
        manager_group.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)
    
# Delivery Crew Management
class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    
    # GET /api/groups/delivery-crew/users
    def list(self, request):
        users = User.objects.filter(groups__name='Delivery Crew')
        return Response([user.username for user in users])

    # POST /api/groups/delivery-crew/users
    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        dc_group = Group.objects.get(name='Delivery Crew')
        dc_group.user_set.add(user)
        return Response(status=status.HTTP_201_CREATED)
    
    # DELETE /api/groups/delivery-crew/users/{userId}
    def destroy(self, request, userId=None):
        user = get_object_or_404(User, id=userId)
        dc_group = Group.objects.get(name="Delivery Crew")
        dc_group.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)
    
# /api/categories
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsManager()]

# /api/menu-items
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['price', 'category']
    search_fields = ['title', 'category__title']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsManager()]
    
# # /api/menu-items/{menuItem}
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsManager()]
