from rest_framework import permissions
from delivery_crew.services import is_delivery_crew

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_delivery_crew(request.user)

class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.groups.filter(name__in=['Manager', 'Delivery Crew']).exists()