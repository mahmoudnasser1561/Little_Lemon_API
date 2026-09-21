import os
from getpass import getpass

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from restaurant.models import ManagerUser, DeliveryCrewUser


def create_customer(username, password, email=''):
    user = User(username=username, email=email)
    validate_password(password, user)
    user.set_password(password)
    user.full_clean()
    user.save()
    return user


ROLES = {
    'manager': ManagerUser.objects.create_user,
    'crew': DeliveryCrewUser.objects.create_user,
    'customer': create_customer,
}


class Command(BaseCommand):
    help = 'Create a manager, delivery crew or customer user'

    def add_arguments(self, parser):
        parser.add_argument('--role', required=True, choices=list(ROLES))
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', default='')

    def handle(self, *args, **options):
        password = os.environ.get('DJANGO_USER_PASSWORD') or self.prompt_password()
        try:
            ROLES[options['role']](options['username'], password, options['email'])
        except ValidationError as e:
            raise CommandError('; '.join(e.messages))
        self.stdout.write(self.style.SUCCESS(f"{options['role']} '{options['username']}' created"))

    def prompt_password(self):
        password = getpass('Password: ')
        if password != getpass('Password (again): '):
            raise CommandError('Passwords do not match.')
        return password
