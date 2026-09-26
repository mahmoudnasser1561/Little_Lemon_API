from django.contrib.auth.models import User
from restaurant.models import RoleUserManager

class DeliveryCrewUserManager(RoleUserManager):
    role = 'Delivery Crew'

class DeliveryCrewUser(User):
    objects = DeliveryCrewUserManager()

    class Meta:
        proxy = True
