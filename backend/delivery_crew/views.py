from rest_framework import status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from restaurant.permissions import IsManager
from .models import DeliveryCrewUser
from .serializers import DeliveryCrewUserSerializer
from .services import get_delivery_crew, remove_delivery_crew

# Delivery Crew Management
class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]

    # GET /api/groups/delivery-crew/users
    def list(self, request):
        users = get_delivery_crew()
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
        remove_delivery_crew(user)
        return Response(status=status.HTTP_200_OK)
