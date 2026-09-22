from rest_framework import serializers
from .models import Cart, MAX_QUANTITY_PER_LINE

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
            'quantity': {'min_value': 1, 'max_value': MAX_QUANTITY_PER_LINE},
            'price': {'read_only': True}
        }

class CartItemSerializer(serializers.ModelSerializer):
    """Read-only view of a cart line. Prices are always read live from the menu, never from the stored copy."""
    title = serializers.CharField(source='menuitem.title', read_only=True)
    unit_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['menuitem', 'title', 'unit_price', 'quantity', 'price']

    def get_unit_price(self, cart_item):
        return str(cart_item.menuitem.price)

    def get_price(self, cart_item):
        return str(cart_item.quantity * cart_item.menuitem.price)
