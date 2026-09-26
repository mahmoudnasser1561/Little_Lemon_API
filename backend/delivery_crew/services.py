from django.contrib.auth.models import Group
from .models import DeliveryCrewUser

# Public interface of the delivery crew module: other modules (e.g. orders) use these
# functions instead of reading the Delivery Crew group or the crew model directly.

def is_delivery_crew(user):
    return user.groups.filter(name='Delivery Crew').exists()

def get_delivery_crew():
    return DeliveryCrewUser.objects.all()

def remove_delivery_crew(user):
    Group.objects.get(name='Delivery Crew').user_set.remove(user)
