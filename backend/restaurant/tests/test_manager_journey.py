import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from rest_framework import status
from rest_framework.authtoken.models import Token

from LittleLemonAPI.testing import PASSWORD, BaseAPITestCase
from restaurant.models import Category, MenuItem

LOGIN = '/api/api-token-auth/'
LOGOUT = '/token/logout/'
MENU = '/api/menu-items/'
CATEGORIES = '/api/categories/'
MANAGERS = '/api/groups/manager/users'


class ManagerPublishesMenuItemsJourneyTests(BaseAPITestCase):
    """
    A manager, created through the CLI, logs in, adds new menu items to a catalog
    that already has some, logs out, and an anonymous visitor who never logged in
    sees the old and the new items together - but has none of the manager's power.
    """

    def create_manager_via_cli(self, username):
        with mock.patch.dict(os.environ, {'DJANGO_USER_PASSWORD': PASSWORD}):
            call_command('create_user', role='manager', username=username, stdout=StringIO())

    def setUp(self):
        super().setUp()
        mains = Category.objects.create(slug='mains', title='Mains')
        MenuItem.objects.create(title='Old Lasagna', price='18.00', featured=False, category=mains)
        MenuItem.objects.create(title='Old Soup', price='6.50', featured=False, category=mains)
        self.create_manager_via_cli('boss')

    def test_the_full_journey(self):
        # 1: the manager, created via the CLI, logs in
        response = self.client_for().post(LOGIN, {'username': 'boss', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['token']
        client = self.client_for()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # 2: the manager creates new menu items
        category = client.post(CATEGORIES, {'slug': 'desserts', 'title': 'Desserts'}, format='json')
        self.assertEqual(category.status_code, status.HTTP_201_CREATED)
        for title, price in (('New Tiramisu', '7.50'), ('New Cheesecake', '8.25')):
            response = client.post(MENU, {'title': title, 'price': price, 'featured': False, 'category_id': category.data['id']}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 3: the manager logs out - the token is revoked immediately
        self.assertIn(client.post(LOGOUT).status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))
        self.assertFalse(Token.objects.filter(key=token).exists())
        self.assertEqual(client.get(MENU).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(client.post(MENU, {'title': 'x', 'price': '1', 'featured': False, 'category_id': category.data['id']}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)

        # 4: a brand-new anonymous visitor, who never logged in, browses the feed
        anonymous = self.client_for()
        titles = sorted(item['title'] for item in self.list_all(anonymous, MENU))
        self.assertEqual(titles, sorted(['Old Lasagna', 'Old Soup', 'New Tiramisu', 'New Cheesecake']))
        prices = {item['title']: item['price'] for item in self.list_all(anonymous, MENU)}
        self.assertEqual((prices['New Tiramisu'], prices['New Cheesecake']), ('7.50', '8.25'))

        # 5: the anonymous visitor has none of the manager's power
        self.assertEqual(anonymous.post(MENU, {'title': 'hack', 'price': '0.01', 'featured': False, 'category_id': category.data['id']}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(anonymous.get(MANAGERS).status_code, status.HTTP_401_UNAUTHORIZED)

        # 6: the manager's role survives the whole cycle
        response = self.client_for().post(LOGIN, {'username': 'boss', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])
        self.assertIn('boss', [user['username'] for user in client.get(MANAGERS).data])
