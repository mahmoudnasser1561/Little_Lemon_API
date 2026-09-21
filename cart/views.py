from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Cart
from .serializers import CartSerializer
from .services import get_cart_items, clear_cart

# Cart Management
# /api/cart/menu-items
class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_cart_items(self.request.user)

    def delete(self, request, *args, **kwargs):
        clear_cart(self.request.user)
        return Response("ok")
