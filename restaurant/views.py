from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .permissions import IsManager
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, UserSerializer

# Manager Group Management
class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    
    # GET /api/groups/manager/users
    def list(self, request):
        users = User.objects.all().filter(groups__name='Manager')
        items = UserSerializer(users, many=True)
        return Response(items.data)

    # POST /api/groups/manager/users
    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.add(user)
        return Response({"message": "user added to the manager group"}, status=status.HTTP_201_CREATED)

    # DELETE /api/groups/manager/users/{userId}
    def destroy(self, request, userId=None):
        user = get_object_or_404(User, id=userId)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return Response({"message": "user removed from the manager group"}, status=status.HTTP_200_OK)
    
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
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsManager]
        return [permission() for permission in permission_classes]

# /api/menu-items
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all().order_by("id")
    serializer_class = MenuItemSerializer
    search_fields = ['category__title']
    ordering_fields = ['price', 'inventory']

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
# /api/menu-items/{menuItem}
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

# Cart Management
# /api/cart/menu-items
class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.all().filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        Cart.objects.all().filter(user=self.request.user).delete()
        return Response("ok")

# Order Management
class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all()
        elif self.request.user.groups.count()==0: #normal customer - no group
            return Order.objects.all().filter(user=self.request.user)
        elif self.request.user.groups.filter(name='Delivery Crew').exists(): #delivery crew
            return Order.objects.all().filter(delivery_crew=self.request.user)  #only show oreders assigned to him
        else: #delivery crew or manager
            return Order.objects.all()
        # else:
        #     return Order.objects.all()

    def create(self, request, *args, **kwargs):
        menuitem_count = Cart.objects.all().filter(user=self.request.user).count()
        if menuitem_count == 0:
            return Response({"message:": "no item in cart"})

        data = request.data.copy()
        total = self.get_total_price(self.request.user)
        data['total'] = total
        data['user'] = self.request.user.id
        order_serializer = OrderSerializer(data=data)
        if (order_serializer.is_valid()):
            order = order_serializer.save()

            items = Cart.objects.all().filter(user=self.request.user).all()

            for item in items.values():
                orderitem = OrderItem(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    unit_price=item['unit_price'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                orderitem.save()

            Cart.objects.all().filter(user=self.request.user).delete()
            return Response(order_serializer.data)
    
    def get_total_price(self, user):
        total = 0
        items = Cart.objects.all().filter(user=user).all()
        for item in items.values():
            total += item['price']
        return total



class SingleOrderView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if self.request.user.groups.count()==0: # Normal user, not belonging to any group = Customer
            return Response('Not Ok')
        else: #everyone else - Super Admin, Manager and Delivery Crew
            return super().update(request, *args, **kwargs)
