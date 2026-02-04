from rest_framework import generics, status, viewsets, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .permissions import IsManager


class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]
    def list(self, request):
        users = User.objects.filter(groups__name='Manager')
        return Response([user.username for user in users])

    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.add(user)
        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)
