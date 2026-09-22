from rest_framework import serializers
from .models import Cart

class CartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, attrs):
        attrs['unit_price'] = attrs['menuitem'].price
        attrs['price'] = attrs['quantity'] * attrs['unit_price']
        return attrs

    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'unit_price', 'quantity', 'price']
        extra_kwargs = {
            'unit_price': {'read_only': True},
            'quantity': {'min_value': 1},
            'price': {'read_only': True}
        }

class CartItemSerializer(serializers.ModelSerializer):
    """Read-only view of a cart line, including the product's name."""
    title = serializers.CharField(source='menuitem.title', read_only=True)

    class Meta:
        model = Cart
        fields = ['menuitem', 'title', 'unit_price', 'quantity', 'price']
