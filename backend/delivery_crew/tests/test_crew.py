from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIRequestFactory

from delivery_crew.models import DeliveryCrewUser
from delivery_crew.permissions import IsDeliveryCrew
from delivery_crew.services import get_delivery_crew, is_delivery_crew, remove_delivery_crew
from LittleLemonAPI.testing import PASSWORD, BaseAPITestCase

CREW = '/api/groups/delivery-crew/users'
MANAGERS = '/api/groups/manager/users'
LOGIN = '/api/api-token-auth/'


class DeliveryCrewRoleModelTests(BaseAPITestCase):
    def test_creating_a_crew_member_puts_them_in_the_delivery_crew_group(self):
        crew = DeliveryCrewUser.objects.create_user('driver', PASSWORD, email='driver@example.com')
        self.assertEqual(list(crew.groups.values_list('name', flat=True)), ['Delivery Crew'])
        self.assertIsInstance(crew, DeliveryCrewUser)

    def test_the_password_is_hashed_and_usable(self):
        crew = self.make_crew()
        self.assertNotEqual(crew.password, PASSWORD)
        self.assertTrue(crew.check_password(PASSWORD))
        response = self.client_for().post(LOGIN, {'username': 'crew', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_crew_list_only_holds_delivery_crew(self):
        self.make_customer('customer'), self.make_manager('boss')
        self.make_crew('driver')
        self.assertEqual(list(DeliveryCrewUser.objects.values_list('username', flat=True)), ['driver'])

    def test_invalid_crew_members_are_rejected_and_nothing_is_created(self):
        self.make_customer('customer'), self.make_manager('boss')
        for label, kwargs in (
            ('weak password', {'username': 'weak', 'password': '123'}),
            ('blank password', {'username': 'blank', 'password': ''}),
            ('username of a customer', {'username': 'customer', 'password': PASSWORD}),
            ('username of a manager', {'username': 'boss', 'password': PASSWORD}),
            ('bad email', {'username': 'mail', 'password': PASSWORD, 'email': 'nope'}),
            ('empty username', {'username': '', 'password': PASSWORD}),
        ):
            with self.subTest(label):
                before = User.objects.count()
                with self.assertRaises(ValidationError):
                    DeliveryCrewUser.objects.create_user(**kwargs)
                self.assertEqual(User.objects.count(), before)

    def test_a_password_is_required(self):
        with self.assertRaises(TypeError):
            DeliveryCrewUser.objects.create_user('nopassword')

    def test_no_half_created_crew_member_when_the_group_is_missing(self):
        Group.objects.filter(name='Delivery Crew').delete()
        with self.assertRaises(Group.DoesNotExist):
            DeliveryCrewUser.objects.create_user('orphan', PASSWORD)
        self.assertFalse(User.objects.filter(username='orphan').exists())


class DeliveryCrewServicesTests(BaseAPITestCase):
    """The public interface of the delivery crew module, used by orders."""

    def test_is_delivery_crew(self):
        self.assertTrue(is_delivery_crew(self.make_crew()))
        for user in (self.make_manager(), self.make_customer(), AnonymousUser()):
            self.assertFalse(is_delivery_crew(user))

    def test_get_delivery_crew_only_returns_crew(self):
        self.make_customer(), self.make_manager()
        self.make_crew('driver1'), self.make_crew('driver2')
        self.assertEqual(sorted(user.username for user in get_delivery_crew()), ['driver1', 'driver2'])

    def test_remove_delivery_crew_removes_the_role_but_keeps_the_account(self):
        crew = self.make_crew()
        remove_delivery_crew(crew)
        self.assertFalse(is_delivery_crew(crew))
        self.assertTrue(User.objects.filter(pk=crew.pk).exists())

    def test_the_is_delivery_crew_permission(self):
        request = APIRequestFactory().get('/')
        for user, expected in ((self.make_crew(), True), (self.make_manager(), False), (self.make_customer(), False), (AnonymousUser(), False)):
            request.user = user
            self.assertEqual(IsDeliveryCrew().has_permission(request, None), expected)


class CreateDeliveryCrewEndpointTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.manager = self.make_manager()
        self.client = self.client_for(self.manager)

    def new_crew(self, **overrides):
        return {'username': 'driver', 'password': PASSWORD, 'email': 'driver@example.com', **overrides}

    def test_a_manager_can_create_a_delivery_crew_account(self):
        response = self.client.post(CREW, self.new_crew(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual((response.data['username'], response.data['email']), ('driver', 'driver@example.com'))
        self.assertNotIn('password', response.data)
        self.assertEqual(list(User.objects.get(username='driver').groups.values_list('name', flat=True)), ['Delivery Crew'])

    def test_the_new_crew_member_can_log_in(self):
        self.client.post(CREW, self.new_crew(), format='json')
        response = self.client_for().post(LOGIN, {'username': 'driver', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_email_is_optional(self):
        self.assertEqual(self.client.post(CREW, self.new_crew(email=''), format='json').status_code, status.HTTP_201_CREATED)

    def test_only_managers_can_create_crew_accounts(self):
        for who, user, expected in (('anonymous', None, 401), ('customer', self.make_customer(), 403), ('delivery crew', self.make_crew('other'), 403)):
            with self.subTest(who):
                self.assertEqual(self.client_for(user).post(CREW, self.new_crew(), format='json').status_code, expected)
        self.assertFalse(User.objects.filter(username='driver').exists())

    def test_invalid_accounts_are_rejected_and_nothing_is_created(self):
        self.make_customer('customer'), self.make_crew('existing')
        for label, body in (
            ('empty body', {}),
            ('no password', {'username': 'x'}),
            ('no username', {'password': PASSWORD}),
            ('weak password', self.new_crew(password='123')),
            ('bad email', self.new_crew(email='nope')),
            ('username of a customer', self.new_crew(username='customer')),
            ('username of a crew member', self.new_crew(username='existing')),
            ('username of a manager', self.new_crew(username='manager')),
        ):
            with self.subTest(label):
                before = User.objects.count()
                self.assertEqual(self.client.post(CREW, body, format='json').status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(User.objects.count(), before)

    def test_privileged_fields_in_the_request_are_ignored(self):
        self.client.post(CREW, self.new_crew(is_superuser=True, is_staff=True, groups=[Group.objects.get(name='Manager').id]), format='json')
        user = User.objects.get(username='driver')
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(list(user.groups.values_list('name', flat=True)), ['Delivery Crew'])


class ListAndRemoveDeliveryCrewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.manager = self.make_manager()
        self.customer = self.make_customer()
        self.driver = self.make_crew('driver')
        self.client = self.client_for(self.manager)

    def test_a_manager_can_list_the_crew(self):
        self.make_crew('driver2')
        response = self.client.get(CREW)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(response.data), ['driver', 'driver2'])

    def test_only_managers_can_list_the_crew(self):
        for user, expected in ((None, 401), (self.customer, 403), (self.driver, 403)):
            with self.subTest(user=user):
                self.assertEqual(self.client_for(user).get(CREW).status_code, expected)

    def test_a_manager_can_remove_a_crew_member(self):
        self.assertEqual(self.client.delete(f'{CREW}/{self.driver.id}').status_code, status.HTTP_200_OK)
        self.assertFalse(is_delivery_crew(User.objects.get(pk=self.driver.pk)))

    def test_a_removed_crew_member_keeps_their_account(self):
        self.client.delete(f'{CREW}/{self.driver.id}')
        self.assertTrue(User.objects.filter(pk=self.driver.pk).exists())

    def test_removing_someone_who_is_no_longer_crew_is_not_found(self):
        self.client.delete(f'{CREW}/{self.driver.id}')
        self.assertEqual(self.client.delete(f'{CREW}/{self.driver.id}').status_code, status.HTTP_404_NOT_FOUND)

    def test_the_crew_endpoint_cannot_remove_managers_or_customers(self):
        for label, user in (('a manager', self.manager), ('a customer', self.customer)):
            with self.subTest(label):
                groups_before = sorted(user.groups.values_list('name', flat=True))
                self.assertEqual(self.client.delete(f'{CREW}/{user.id}').status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(sorted(user.groups.values_list('name', flat=True)), groups_before)

    def test_nobody_else_can_remove_a_crew_member(self):
        for who, user, expected in (('anonymous', None, 401), ('customer', self.customer, 403), ('delivery crew', self.make_crew('other'), 403)):
            with self.subTest(who):
                self.assertEqual(self.client_for(user).delete(f'{CREW}/{self.driver.id}').status_code, expected)
        self.assertTrue(is_delivery_crew(self.driver))


class DeliveryCrewAccessTests(BaseAPITestCase):
    """Delivery crew only get their assigned orders: no customer data, no management."""

    def test_a_crew_member_only_sees_their_own_account(self):
        crew = self.make_crew()
        other = self.make_customer('other')
        client = self.client_for(crew)
        self.assertEqual([user['username'] for user in client.get('/api/users/').data['results']], ['crew'])
        self.assertEqual(client.get(f'/api/users/{other.id}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_a_crew_member_cannot_reach_the_management_endpoints(self):
        client = self.client_for(self.make_crew())
        self.assertEqual(client.get(MANAGERS).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client.get(CREW).status_code, status.HTTP_403_FORBIDDEN)
