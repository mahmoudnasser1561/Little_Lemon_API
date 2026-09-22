from rest_framework import serializers
from .models import Cart, MAX_QUANTITY_PER_LINE

class CartSerializer(serializers.ModelSerializer):
    """Validates a request to add an item to the cart. The price is never taken from the client (see services.py)."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity']
        extra_kwargs = {
            'quantity': {'min_value': 1, 'max_value': MAX_QUANTITY_PER_LINE},
        }
        validators = []  # adding an item already in the cart merges the quantity (view), not a 400

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
