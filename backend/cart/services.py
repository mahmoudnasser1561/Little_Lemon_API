from decimal import Decimal

from .models import Cart

# Public interface of the cart module: other modules (e.g. checkout) use these
# functions instead of querying the Cart model directly.
# The total is always read live from the menu, never from a cart row's stored price.

def get_cart_items(user):
    return Cart.objects.filter(user=user).select_related('menuitem')

def get_cart_total(user):
    return sum((item.quantity * item.menuitem.price for item in get_cart_items(user)), Decimal('0.00'))

def clear_cart(user):
    get_cart_items(user).delete()
