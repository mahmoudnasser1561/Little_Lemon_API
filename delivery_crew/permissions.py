from rest_framework import permissions

class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Delivery Crew').exists()
