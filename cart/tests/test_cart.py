from django.db import IntegrityError, transaction
from rest_framework import status

from cart.models import MAX_QUANTITY_PER_LINE, Cart
from cart.services import clear_cart, get_cart_items, get_cart_total
from LittleLemonAPI.testing import BaseAPITestCase, known_bug
from restaurant.models import MenuItem

CART = '/api/cart/menu-items'


class CartTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.alice = self.make_customer('alice')
        self.bob = self.make_customer('bob')
        self.salad = self.make_menu_item('Greek Salad', '12.50')
        self.steak = self.make_menu_item('Steak', '20.00')
        self.soup = self.make_menu_item('Soup', '6.50')

    def add(self, client, item, quantity=1, **extra):
        return client.post(CART, {'menuitem': item.id, 'quantity': quantity, **extra}, format='json')

    def cart_lines(self, client):
        return client.get(CART).data['items']

    def cart_summary(self, client):
        return sorted((line['menuitem'], line['quantity'], line['price']) for line in self.cart_lines(client))


class AddToCartTests(CartTestCase):
    def test_a_customer_can_add_a_menu_item(self):
        response = self.add(self.client_for(self.alice), self.salad, 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual((response.data['menuitem'], response.data['quantity']), (self.salad.id, 2))
        self.assertEqual((response.data['unit_price'], response.data['price']), ('12.50', '25.00'))

    def test_the_line_belongs_to_the_customer_who_added_it(self):
        self.add(self.client_for(self.alice), self.salad)
        self.assertEqual(Cart.objects.get().user, self.alice)

    def test_any_menu_item_can_be_added(self):
        client = self.client_for(self.alice)
        for item in (self.salad, self.steak, self.soup):
            self.assertEqual(self.add(client, item).status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.cart_lines(client)), 3)

    def test_the_price_comes_from_the_menu_not_from_the_client(self):
        response = self.add(self.client_for(self.alice), self.salad, 1, unit_price='0.01', price='0.01')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual((response.data['unit_price'], response.data['price']), ('12.50', '12.50'))
        self.assertEqual(str(Cart.objects.get().unit_price), '12.50')

    def test_the_quantity_must_be_at_least_one(self):
        client = self.client_for(self.alice)
        for label, quantity in (('zero', 0), ('negative', -3), ('text', 'abc'), ('missing', None)):
            with self.subTest(label):
                body = {'menuitem': self.salad.id}
                if quantity is not None:
                    body['quantity'] = quantity
                self.assertEqual(client.post(CART, body, format='json').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cart.objects.count(), 0)

    def test_an_unknown_menu_item_is_rejected(self):
        response = self.client_for(self.alice).post(CART, {'menuitem': 999, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_user_cannot_add_to_a_cart(self):
        self.assertEqual(self.add(self.client_for(), self.salad).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_the_owner_of_a_line_cannot_be_chosen_by_the_client(self):
        self.add(self.client_for(self.bob), self.salad, user=self.alice.id)
        self.assertEqual(Cart.objects.filter(user=self.alice).count(), 0)
        self.assertEqual(Cart.objects.filter(user=self.bob).count(), 1)

    def test_the_cart_shows_the_current_menu_price_even_if_it_changed_after_adding(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad, 2)
        MenuItem.objects.filter(pk=self.salad.pk).update(price='15.00')
        line = self.cart_lines(client)[0]
        self.assertEqual((line['unit_price'], line['price']), ('15.00', '30.00'))
        self.assertEqual(client.get(CART).data['total'], '30.00')

    def test_a_huge_quantity_is_not_a_server_error(self):
        """The cart side of B11: a single line's quantity is capped, so it can no longer overflow the price field."""
        self.assertLess(self.add(self.client_for(self.alice), self.salad, 1000).status_code, 500)

    def test_a_quantity_above_the_cap_is_rejected(self):
        self.assertEqual(self.add(self.client_for(self.alice), self.salad, 100).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cart.objects.count(), 0)

    def test_a_quantity_at_the_cap_is_accepted(self):
        response = self.add(self.client_for(self.alice), self.salad, MAX_QUANTITY_PER_LINE)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_adding_an_item_that_is_already_in_the_cart_adds_to_its_quantity(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad, 1)
        response = self.add(client, self.salad, 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart_summary(client), [(self.salad.id, 3, '37.50')])

    def test_the_combined_quantity_cannot_go_over_the_cap(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad, 60)
        response = self.add(client, self.salad, 50)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.cart_summary(client), [(self.salad.id, 60, '750.00')])


class ViewCartTests(CartTestCase):
    def test_the_cart_lists_the_customers_lines(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad, 2)
        self.add(client, self.steak, 1)
        self.assertEqual(self.cart_summary(client), sorted([(self.salad.id, 2, '25.00'), (self.steak.id, 1, '20.00')]))

    def test_an_empty_cart_is_empty(self):
        self.assertEqual(self.cart_lines(self.client_for(self.alice)), [])

    def test_anonymous_user_has_no_cart(self):
        self.assertEqual(self.client_for().get(CART).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_the_cart_shows_the_total(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad, 2)
        self.add(client, self.steak, 1)
        self.assertEqual(client.get(CART).data.get('total'), '45.00')

    def test_an_empty_carts_total_is_zero(self):
        self.assertEqual(self.client_for(self.alice).get(CART).data.get('total'), '0.00')

    def test_the_cart_shows_the_product_names(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad)
        self.assertEqual([line.get('title') for line in self.cart_lines(client)], ['Greek Salad'])

    def test_the_whole_cart_comes_back_in_one_response(self):
        client = self.client_for(self.alice)
        for item in (self.salad, self.steak, self.soup):
            self.add(client, item)
        self.assertEqual(len(client.get(CART).data['items']), 3)

    @known_bug('C3')
    def test_a_line_can_be_changed_to_another_quantity(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad, 1)
        self.assertEqual(client.patch(f'{CART}/{self.salad.id}', {'quantity': 5}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart_summary(client), [(self.salad.id, 5, '62.50')])

    @known_bug('C3')
    def test_a_single_line_can_be_removed(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad)
        self.add(client, self.steak)
        self.assertLess(client.delete(f'{CART}/{self.salad.id}').status_code, 300)
        self.assertEqual([line['menuitem'] for line in self.cart_lines(client)], [self.steak.id])


class ClearCartTests(CartTestCase):
    def test_a_customer_can_empty_their_cart(self):
        client = self.client_for(self.alice)
        self.add(client, self.salad)
        self.add(client, self.steak)
        self.assertEqual(client.delete(CART).status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart_lines(client), [])

    def test_emptying_a_cart_leaves_other_carts_alone(self):
        self.add(self.client_for(self.alice), self.salad)
        bob = self.client_for(self.bob)
        self.add(bob, self.steak)
        bob.delete(CART)
        self.assertEqual(Cart.objects.filter(user=self.alice).count(), 1)

    def test_anonymous_user_cannot_empty_a_cart(self):
        self.add(self.client_for(self.alice), self.salad)
        self.assertEqual(self.client_for().delete(CART).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Cart.objects.count(), 1)


class CartPrivacyTests(CartTestCase):
    def setUp(self):
        super().setUp()
        self.add(self.client_for(self.alice), self.salad, 2)
        self.add(self.client_for(self.alice), self.steak, 1)
        self.add(self.client_for(self.bob), self.soup, 1)

    def test_a_customer_only_sees_their_own_cart(self):
        self.assertEqual([line['menuitem'] for line in self.cart_lines(self.client_for(self.bob))], [self.soup.id])
        self.assertEqual(sorted(line['menuitem'] for line in self.cart_lines(self.client_for(self.alice))), sorted([self.salad.id, self.steak.id]))

    def test_query_parameters_cannot_reveal_another_cart(self):
        client = self.client_for(self.bob)
        for query in (f'?user={self.alice.id}', f'?user__id={self.alice.id}', '?search=alice', '?ordering=-user', f'?menuitem={self.salad.id}'):
            with self.subTest(query):
                self.assertEqual([line['menuitem'] for line in client.get(CART + query).data['items']], [self.soup.id])

    def test_a_customer_cannot_change_or_remove_a_line_they_do_not_have(self):
        client = self.client_for(self.bob)
        self.assertEqual(client.patch(f'{CART}/{self.salad.id}', {'quantity': 9}, format='json').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(client.delete(f'{CART}/{self.salad.id}').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Cart.objects.get(user=self.alice, menuitem=self.salad).quantity, 2)

    def test_a_manager_only_sees_their_own_cart(self):
        self.assertEqual(self.cart_lines(self.client_for(self.make_manager())), [])


class CartServicesTests(CartTestCase):
    """The public interface of the cart module, used by checkout."""

    def setUp(self):
        super().setUp()
        Cart.objects.create(user=self.alice, menuitem=self.salad, quantity=2, unit_price='12.50', price='25.00')
        Cart.objects.create(user=self.alice, menuitem=self.steak, quantity=1, unit_price='20.00', price='20.00')
        Cart.objects.create(user=self.bob, menuitem=self.soup, quantity=1, unit_price='6.50', price='6.50')

    def test_get_cart_items_only_returns_the_users_lines(self):
        self.assertEqual(sorted(item.menuitem.title for item in get_cart_items(self.alice)), ['Greek Salad', 'Steak'])
        self.assertEqual([item.menuitem.title for item in get_cart_items(self.bob)], ['Soup'])

    def test_get_cart_total_adds_up_the_line_prices(self):
        self.assertEqual(str(get_cart_total(self.alice)), '45.00')
        self.assertEqual(str(get_cart_total(self.bob)), '6.50')

    def test_the_total_of_an_empty_cart_is_zero(self):
        self.assertEqual(get_cart_total(self.make_customer('carol')), 0)

    def test_the_total_uses_the_current_menu_price(self):
        MenuItem.objects.filter(pk=self.salad.pk).update(price='15.00')
        self.assertEqual(str(get_cart_total(self.alice)), '50.00')  # 2 x 15.00 + 1 x 20.00

    def test_clear_cart_only_clears_the_users_cart(self):
        clear_cart(self.alice)
        self.assertEqual(get_cart_items(self.alice).count(), 0)
        self.assertEqual(get_cart_items(self.bob).count(), 1)

    def test_a_user_has_one_line_per_menu_item(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Cart.objects.create(user=self.alice, menuitem=self.salad, quantity=1, unit_price='12.50', price='12.50')
