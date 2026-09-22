import os
import unittest

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from delivery_crew.models import DeliveryCrewUser
from restaurant.models import Category, ManagerUser, MenuItem

PASSWORD = 'Str0ngPass!9'


def known_bug(bug_id):
    """
    Marks a test that describes the DESIRED behaviour of a bug or feature that is still open in API_WORK_PLAN.md.
    The test is reported as an expected failure. When the bug is fixed the runner reports an "unexpected success":
    remove the decorator and the test becomes a normal regression test.
    Run with SHOW_KNOWN_BUGS=1 to run these tests as normal tests and see why they fail.
    """
    def decorator(test):
        test.__doc__ = f'[known bug {bug_id}] ' + (test.__doc__ or test.__name__)
        if os.environ.get('SHOW_KNOWN_BUGS'):
            return test
        return unittest.expectedFailure(test)
    return decorator


# Hashing passwords with the default hasher is slow on purpose, tests use a fast one
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BaseAPITestCase(APITestCase):
    password = PASSWORD

    def setUp(self):
        cache.clear()  # forget the throttling counters of the previous tests

    # Users
    def make_customer(self, username='customer', **extra):
        return User.objects.create_user(username, password=self.password, **extra)

    def make_manager(self, username='manager'):
        return ManagerUser.objects.create_user(username, self.password)

    def make_crew(self, username='crew'):
        return DeliveryCrewUser.objects.create_user(username, self.password)

    def make_superuser(self, username='root'):
        return User.objects.create_superuser(username, password=self.password)

    def client_for(self, user=None):
        """A client logged in as user with a token, or an anonymous client. 500 errors come back as responses."""
        client = APIClient(raise_request_exception=False)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return client

    def list_all(self, client, url):
        """Every item of a paginated list, following the next links."""
        items, next_url = [], url
        while next_url:
            response = client.get(next_url)
            self.assertEqual(response.status_code, 200)
            items += response.data['results']
            next_url = response.data['next']
        return items

    # Menu
    def make_menu_item(self, title='Greek Salad', price='12.50', category=None, featured=False):
        category = category or Category.objects.get_or_create(slug='mains', title='Mains')[0]
        return MenuItem.objects.create(title=title, price=price, featured=featured, category=category)
