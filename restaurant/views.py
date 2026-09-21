from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .permissions import IsManager
from .models import Category, MenuItem, Order, OrderItem, DeliveryCrewUser
from .serializers import CategorySerializer, MenuItemSerializer, OrderSerializer, UserSerializer, DeliveryCrewUserSerializer
from cart.services import get_cart_items, get_cart_total, clear_cart

# Manager Group Management
class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    
    # GET /api/groups/manager/users
    def list(self, request):
        users = User.objects.all().filter(groups__name='Manager')
        items = UserSerializer(users, many=True)
        return Response(items.data)

# Delivery Crew Management
class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    
    # GET /api/groups/delivery-crew/users
    def list(self, request):
        users = User.objects.filter(groups__name='Delivery Crew')
        return Response([user.username for user in users])

    # POST /api/groups/delivery-crew/users
    def create(self, request):
        serializer = DeliveryCrewUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # DELETE /api/groups/delivery-crew/users/{userId}
    def destroy(self, request, userId=None):
        user = get_object_or_404(DeliveryCrewUser, id=userId)
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
            permission_classes = [IsAuthenticated, IsManager]

        return [permission() for permission in permission_classes]
    
# /api/menu-items/{menuItem}
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsManager]

        return [permission() for permission in permission_classes]

# Order Management
# Managers see all orders, delivery crew only their assigned orders, everyone else only their own
class OrderQuerysetMixin:
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)

class OrderView(OrderQuerysetMixin, generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        menuitem_count = get_cart_items(self.request.user).count()
        if menuitem_count == 0:
            return Response({"message:": "no item in cart"})

        data = request.data.copy()
        total = get_cart_total(self.request.user)
        data['total'] = total
        data['user'] = self.request.user.id
        order_serializer = OrderSerializer(data=data)
        if (order_serializer.is_valid()):
            order = order_serializer.save()

            items = get_cart_items(self.request.user)

            for item in items.values():
                orderitem = OrderItem(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    unit_price=item['unit_price'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                orderitem.save()

            clear_cart(self.request.user)
            return Response(order_serializer.data)



class SingleOrderView(OrderQuerysetMixin, generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if self.request.user.groups.count()==0: # Normal user, not belonging to any group = Customer
            return Response('Not Ok')
        else: #everyone else - Super Admin, Manager and Delivery Crew
            return super().update(request, *args, **kwargs)
