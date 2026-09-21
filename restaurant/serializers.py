from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, MenuItem, OrderItem, Order
from delivery_crew.services import is_delivery_crew

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']
        
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    orderitem = OrderItemSerializer(many=True, read_only=True, source='order')

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew',
                  'status', 'date', 'total', 'orderitem']

# Managers only manage the delivery side of an order (crew assignment and status), customer data is read-only
class OrderUpdateSerializer(OrderSerializer):
    class Meta(OrderSerializer.Meta):
        read_only_fields = ['user', 'total', 'date']

    def validate_delivery_crew(self, value):
        if value is not None and not is_delivery_crew(value):
            raise serializers.ValidationError('User is not a delivery crew member.')
        return value
