from .models import Cart

# Public interface of the cart module: other modules (e.g. checkout) use these
# functions instead of querying the Cart model directly.

def get_cart_items(user):
    return Cart.objects.filter(user=user)

def get_cart_total(user):
    return sum(item.price for item in get_cart_items(user))

def clear_cart(user):
    get_cart_items(user).delete()
