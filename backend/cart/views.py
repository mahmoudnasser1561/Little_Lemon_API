from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Cart, MAX_QUANTITY_PER_LINE
from .serializers import CartSerializer, CartItemSerializer, CartItemUpdateSerializer
from .services import get_cart_items, get_cart_total, clear_cart

# Cart Management
# /api/cart/menu-items
class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # the whole cart comes back in one response

    def get_queryset(self):
        return get_cart_items(self.request.user)

    def list(self, request, *args, **kwargs):
        return Response({
            'items': CartItemSerializer(self.get_queryset(), many=True).data,
            'total': str(get_cart_total(request.user)),
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']

        cart_item, created = Cart.objects.get_or_create(
            user=request.user, menuitem=menuitem,
            defaults={'quantity': quantity, 'unit_price': menuitem.price, 'price': quantity * menuitem.price},
        )
        if not created:
            quantity += cart_item.quantity
            if quantity > MAX_QUANTITY_PER_LINE:
                raise ValidationError({'quantity': f'A single line cannot hold more than {MAX_QUANTITY_PER_LINE}.'})
            cart_item.quantity = quantity
            cart_item.unit_price = menuitem.price
            cart_item.price = quantity * menuitem.price
            cart_item.save()

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        clear_cart(request.user)
        return Response("ok")

# /api/cart/menu-items/{menuitem_id}
class CartItemView(generics.GenericAPIView):
    serializer_class = CartItemUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Cart.objects.select_related('menuitem'), user=self.request.user, menuitem_id=self.kwargs['menuitem_id'])

    def patch(self, request, menuitem_id):
        cart_item = self.get_object()
        serializer = self.get_serializer(cart_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CartItemSerializer(cart_item).data)

    def delete(self, request, menuitem_id):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
