from rest_framework import status
from rest_framework.authtoken.models import Token

from LittleLemonAPI.testing import PASSWORD, BaseAPITestCase

USERS = '/api/users/'
LOGIN = '/api/api-token-auth/'
LOGOUT = '/token/logout/'
MENU = '/api/menu-items/'
CART = '/api/cart/menu-items'


class GuestBrowsesAndOrdersJourneyTests(BaseAPITestCase):
    """
    A guest registers, browses the menu, builds a cart across several visits to the
    feed, logs out and logs back in, and still finds the same cart waiting for them.
    """

    def setUp(self):
        super().setUp()
        self.menu = {
            title: self.make_menu_item(title, price).id
            for title, price in (
                ('Greek Salad', '12.50'), ('Bruschetta', '8.00'), ('Lasagna', '18.00'),
                ('Steak', '32.00'), ('Pasta', '14.25'), ('Tiramisu', '7.50'), ('Cake', '6.00'),
            )
        }

    def login(self, **credentials):
        response = self.client_for().post(LOGIN, credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['token']

    def add_to_cart(self, client, title, quantity):
        response = client.post(CART, {'menuitem': self.menu[title], 'quantity': quantity}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def cart_contents(self, token):
        client = self.client_for()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        return sorted((line['menuitem'], line['quantity']) for line in self.list_all(client, CART))

    def test_the_full_journey(self):
        anonymous = self.client_for()

        # 1: register and log in
        signup = anonymous.post(USERS, {'username': 'diner', 'password': PASSWORD, 'email': 'diner@example.com'}, format='json')
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        token = self.login(username='diner', password=PASSWORD)
        client = self.client_for()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # 2: the feed shows every product
        self.assertEqual(sorted(item['title'] for item in self.list_all(client, MENU)), sorted(self.menu))

        # 3: add an item to the cart
        line = self.add_to_cart(client, 'Greek Salad', 2)
        self.assertEqual((line['unit_price'], line['price']), ('12.50', '25.00'))

        # 4: back to the feed - browsing does not disturb the cart
        self.assertEqual(sorted(item['title'] for item in self.list_all(client, MENU)), sorted(self.menu))
        self.assertEqual(self.cart_contents(token), [(self.menu['Greek Salad'], 2)])

        # 5: add more items while browsing
        self.add_to_cart(client, 'Steak', 1)
        self.add_to_cart(client, 'Tiramisu', 3)

        # 6: the cart shows every line added, each at the menu price
        expected = sorted([(self.menu['Greek Salad'], 2), (self.menu['Steak'], 1), (self.menu['Tiramisu'], 3)])
        cart = self.list_all(client, CART)
        self.assertEqual(sorted((line['menuitem'], line['quantity']) for line in cart), expected)
        self.assertEqual({line['menuitem']: line['unit_price'] for line in cart},
                          {self.menu['Greek Salad']: '12.50', self.menu['Steak']: '32.00', self.menu['Tiramisu']: '7.50'})

        # 7: log out - the token is revoked immediately
        self.assertIn(client.post(LOGOUT).status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))
        self.assertFalse(Token.objects.filter(key=token).exists())
        self.assertEqual(client.get(CART).status_code, status.HTTP_401_UNAUTHORIZED)

        # 8: log back in with a freshly issued token
        new_token = self.login(username='diner', password=PASSWORD)
        self.assertNotEqual(new_token, token)

        # 9: the cart is exactly as it was left before logging out
        self.assertEqual(self.cart_contents(new_token), expected)
