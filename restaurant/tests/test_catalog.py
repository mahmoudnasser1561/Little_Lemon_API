from rest_framework import status

from LittleLemonAPI.testing import BaseAPITestCase, known_bug
from restaurant.models import Category, MenuItem

MENU = '/api/menu-items/'
CATEGORIES = '/api/categories/'


class CatalogTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.customer = self.make_customer()
        self.manager = self.make_manager()
        self.crew = self.make_crew()
        self.mains = Category.objects.create(slug='mains', title='Mains')
        self.desserts = Category.objects.create(slug='desserts', title='Desserts')

    def menu_body(self, **overrides):
        return {'title': 'Soup', 'price': '6.50', 'featured': False, 'category_id': self.mains.id, **overrides}


class PublicCatalogTests(CatalogTestCase):
    def test_anonymous_user_can_see_every_product(self):
        for number in range(5):
            self.make_menu_item(title=f'Dish {number}', category=self.mains)
        items = self.list_all(self.client_for(), MENU)
        self.assertEqual(sorted(item['title'] for item in items), [f'Dish {number}' for number in range(5)])

    def test_a_product_shows_its_price_and_category(self):
        item = self.make_menu_item(title='Greek Salad', price='12.50', category=self.mains, featured=True)
        response = self.client_for().get(f'{MENU}{item.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': item.id, 'title': 'Greek Salad', 'price': '12.50', 'featured': True,
            'category': {'id': self.mains.id, 'slug': 'mains', 'title': 'Mains'},
        })

    def test_unknown_product_is_not_found(self):
        self.assertEqual(self.client_for().get(f'{MENU}999').status_code, status.HTTP_404_NOT_FOUND)

    def test_a_page_beyond_the_last_one_is_not_found(self):
        self.make_menu_item()
        self.assertEqual(self.client_for().get(f'{MENU}?page=99').status_code, status.HTTP_404_NOT_FOUND)

    def test_categories_are_public(self):
        response = self.client_for().get(CATEGORIES)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(category['title'] for category in response.data['results']), ['Desserts', 'Mains'])

    def test_search_matches_the_category_title(self):
        self.make_menu_item(title='Steak', category=self.mains)
        self.make_menu_item(title='Cake', category=self.desserts)
        titles = [item['title'] for item in self.list_all(self.client_for(), f'{MENU}?search=Desserts')]
        self.assertEqual(titles, ['Cake'])

    def test_products_can_be_ordered_by_price(self):
        for title, price in (('Cheap', '5.00'), ('Middle', '10.00'), ('Dear', '20.00'), ('Cheaper', '4.00')):
            self.make_menu_item(title=title, price=price)
        client = self.client_for()
        self.assertEqual([item['title'] for item in self.list_all(client, f'{MENU}?ordering=price')], ['Cheaper', 'Cheap', 'Middle', 'Dear'])
        self.assertEqual([item['title'] for item in self.list_all(client, f'{MENU}?ordering=-price')], ['Dear', 'Middle', 'Cheap', 'Cheaper'])

    @known_bug('B8')
    def test_ordering_by_a_field_that_does_not_exist_is_not_a_server_error(self):
        self.make_menu_item()
        self.assertLess(self.client_for().get(f'{MENU}?ordering=inventory').status_code, 500)

    def test_the_first_page_holds_more_than_two_products(self):
        """B24: PAGE_SIZE was 2, so a handful of items already spanned several pages."""
        for number in range(15):
            self.make_menu_item(title=f'Dish {number}')
        self.assertGreater(len(self.client_for().get(MENU).data['results']), 2)

    def test_page_size_is_client_adjustable_with_a_cap(self):
        """B24: no way to ask for a bigger page was the other half of the complaint."""
        for number in range(60):
            self.make_menu_item(title=f'Dish {number}')
        client = self.client_for()
        self.assertEqual(len(client.get(f'{MENU}?page_size=5').data['results']), 5)
        self.assertEqual(len(client.get(f'{MENU}?page_size=1000').data['results']), 50)  # capped

    @known_bug('B25')
    def test_search_matches_the_dish_name(self):
        self.make_menu_item(title='Lasagna', category=self.mains)
        self.make_menu_item(title='Cake', category=self.desserts)
        titles = [item['title'] for item in self.list_all(self.client_for(), f'{MENU}?search=Lasagna')]
        self.assertEqual(titles, ['Lasagna'])


class MenuItemManagementTests(CatalogTestCase):
    def test_a_manager_can_add_a_menu_item(self):
        response = self.client_for(self.manager).post(MENU, self.menu_body(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Soup')
        self.assertEqual(MenuItem.objects.get(title='Soup').category, self.mains)

    def test_a_manager_can_change_the_price(self):
        item = self.make_menu_item(price='10.00')
        response = self.client_for(self.manager).patch(f'{MENU}{item.id}', {'price': '11.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(str(item.price), '11.00')

    def test_a_manager_can_replace_a_menu_item(self):
        item = self.make_menu_item()
        response = self.client_for(self.manager).put(f'{MENU}{item.id}', self.menu_body(title='Renamed'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.title, 'Renamed')

    def test_a_manager_can_delete_a_menu_item(self):
        item = self.make_menu_item()
        self.assertEqual(self.client_for(self.manager).delete(f'{MENU}{item.id}').status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MenuItem.objects.filter(pk=item.pk).exists())

    def test_nobody_else_can_change_the_menu(self):
        item = self.make_menu_item(price='10.00')
        for who, user, expected in (('anonymous', None, 401), ('customer', self.customer, 403), ('delivery crew', self.crew, 403)):
            client = self.client_for(user)
            with self.subTest(who):
                self.assertEqual(client.post(MENU, self.menu_body(), format='json').status_code, expected)
                self.assertEqual(client.patch(f'{MENU}{item.id}', {'price': '0.01'}, format='json').status_code, expected)
                self.assertEqual(client.put(f'{MENU}{item.id}', self.menu_body(), format='json').status_code, expected)
                self.assertEqual(client.delete(f'{MENU}{item.id}').status_code, expected)
        item.refresh_from_db()
        self.assertEqual((item.title, str(item.price)), ('Greek Salad', '10.00'))
        self.assertEqual(MenuItem.objects.count(), 1)

    def test_a_menu_item_needs_a_category(self):
        body = self.menu_body()
        del body['category_id']
        self.assertEqual(self.client_for(self.manager).post(MENU, body, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    @known_bug('B17')
    def test_a_negative_price_is_rejected(self):
        response = self.client_for(self.manager).post(MENU, self.menu_body(price='-5'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @known_bug('B27')
    def test_featured_is_optional_and_defaults_to_false(self):
        body = self.menu_body()
        del body['featured']
        self.assertEqual(self.client_for(self.manager).post(MENU, body, format='json').status_code, status.HTTP_201_CREATED)


class CategoryManagementTests(CatalogTestCase):
    def test_a_manager_can_add_a_category(self):
        response = self.client_for(self.manager).post(CATEGORIES, {'slug': 'starters', 'title': 'Starters'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(slug='starters').exists())

    def test_nobody_else_can_add_a_category(self):
        for who, user, expected in (('anonymous', None, 401), ('customer', self.customer, 403), ('delivery crew', self.crew, 403)):
            with self.subTest(who):
                response = self.client_for(user).post(CATEGORIES, {'slug': 'x', 'title': 'X'}, format='json')
                self.assertEqual(response.status_code, expected)
        self.assertFalse(Category.objects.filter(slug='x').exists())

    @known_bug('B17')
    def test_a_duplicate_category_slug_is_rejected(self):
        response = self.client_for(self.manager).post(CATEGORIES, {'slug': 'mains', 'title': 'Mains again'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
