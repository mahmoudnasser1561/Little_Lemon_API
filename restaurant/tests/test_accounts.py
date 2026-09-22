import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework import status
from rest_framework.test import APIRequestFactory

from LittleLemonAPI.testing import PASSWORD, BaseAPITestCase, known_bug
from restaurant.models import ManagerUser
from restaurant.permissions import IsCustomer, IsManager

USERS = '/api/users/'
ME = '/api/users/me/'
LOGIN = '/api/api-token-auth/'
DJOSER_LOGIN = '/token/login/'
MANAGERS = '/api/groups/manager/users'


class RegistrationAndLoginTests(BaseAPITestCase):
    def signup(self, client=None, **overrides):
        data = {'username': 'alice', 'password': PASSWORD, 'email': 'alice@example.com', **overrides}
        return (client or self.client_for()).post(USERS, data, format='json')

    def test_customer_can_register(self):
        response = self.signup()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'alice')
        self.assertNotIn('password', response.data)

    def test_registered_customer_can_log_in_with_the_token_endpoint(self):
        self.signup()
        response = self.client_for().post(LOGIN, {'username': 'alice', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_registered_customer_can_log_in_with_the_djoser_endpoint(self):
        self.signup()
        response = self.client_for().post(DJOSER_LOGIN, {'username': 'alice', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_wrong_password_cannot_log_in(self):
        self.signup()
        response = self.client_for().post(LOGIN, {'username': 'alice', 'password': 'wrong'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_customer_has_no_role_and_no_privileges(self):
        self.signup()
        user = User.objects.get(username='alice')
        self.assertEqual(list(user.groups.all()), [])
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_registration_ignores_privileged_fields(self):
        self.signup(is_staff=True, is_superuser=True, groups=[Group.objects.get(name='Manager').id])
        user = User.objects.get(username='alice')
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(list(user.groups.all()), [])

    def test_registration_validates_the_input(self):
        self.signup()
        for label, overrides in (
            ('weak password', {'username': 'bob', 'password': '123'}),
            ('taken username', {'username': 'alice'}),
            ('no password', {'username': 'bob', 'password': ''}),
        ):
            with self.subTest(label):
                self.assertEqual(self.signup(**overrides).status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_is_optional(self):
        self.assertEqual(self.signup(email='').status_code, status.HTTP_201_CREATED)

    @known_bug('B30')
    def test_reset_password_does_not_reveal_which_emails_are_registered(self):
        self.make_customer(email='known@example.com')
        client = self.client_for()
        known = client.post('/api/users/reset_password/', {'email': 'known@example.com'}, format='json')
        unknown = client.post('/api/users/reset_password/', {'email': 'nobody@example.com'}, format='json')
        self.assertEqual(known.status_code, unknown.status_code)

    @known_bug('B30')
    def test_reset_username_does_not_reveal_which_emails_are_registered(self):
        self.make_customer(email='known@example.com')
        client = self.client_for()
        known = client.post('/api/users/reset_username/', {'email': 'known@example.com'}, format='json')
        unknown = client.post('/api/users/reset_username/', {'email': 'nobody@example.com'}, format='json')
        self.assertEqual(known.status_code, unknown.status_code)


class ProfileTests(BaseAPITestCase):
    def test_customer_can_read_and_update_their_own_profile(self):
        customer = self.make_customer()
        client = self.client_for(customer)
        self.assertEqual(client.get(ME).status_code, status.HTTP_200_OK)
        response = client.patch(ME, {'email': 'new@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.email, 'new@example.com')

    def test_customer_cannot_give_themselves_a_role(self):
        customer = self.make_customer()
        manager_group = Group.objects.get(name='Manager')
        self.client_for(customer).patch(ME, {'is_staff': True, 'is_superuser': True, 'groups': [manager_group.id]}, format='json')
        customer.refresh_from_db()
        self.assertFalse(customer.is_staff or customer.is_superuser)
        self.assertEqual(list(customer.groups.all()), [])

    def test_anonymous_user_has_no_profile(self):
        self.assertEqual(self.client_for().get(ME).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_only_sees_their_own_account(self):
        alice, bob = self.make_customer('alice'), self.make_customer('bob')
        client = self.client_for(bob)
        self.assertEqual([user['username'] for user in client.get(USERS).data['results']], ['bob'])
        self.assertEqual(client.get(f'{USERS}{alice.id}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_cannot_edit_another_account(self):
        alice, bob = self.make_customer('alice', email='alice@example.com'), self.make_customer('bob')
        response = self.client_for(bob).patch(f'{USERS}{alice.id}/', {'email': 'hacked@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        alice.refresh_from_db()
        self.assertEqual(alice.email, 'alice@example.com')

    def test_manager_cannot_edit_or_delete_a_customer_account(self):
        customer = self.make_customer(email='customer@example.com')
        client = self.client_for(self.make_manager())
        self.assertIn(client.patch(f'{USERS}{customer.id}/', {'email': 'hacked@example.com'}, format='json').status_code, (403, 404))
        self.assertIn(client.delete(f'{USERS}{customer.id}/', {'current_password': PASSWORD}, format='json').status_code, (403, 404))
        customer.refresh_from_db()
        self.assertEqual(customer.email, 'customer@example.com')


class RolesTests(BaseAPITestCase):
    def has_permission(self, permission, user):
        request = APIRequestFactory().get('/')
        request.user = user
        return permission().has_permission(request, None)

    def test_manager_and_delivery_crew_groups_are_seeded_by_a_migration(self):
        names = set(Group.objects.values_list('name', flat=True))
        self.assertTrue({'Manager', 'Delivery Crew'} <= names)

    def test_is_manager(self):
        self.assertTrue(self.has_permission(IsManager, self.make_manager()))
        for user in (AnonymousUser(), self.make_customer(), self.make_crew()):
            self.assertFalse(self.has_permission(IsManager, user))

    def test_is_customer(self):
        self.assertTrue(self.has_permission(IsCustomer, self.make_customer()))
        for user in (AnonymousUser(), self.make_manager(), self.make_crew()):
            self.assertFalse(self.has_permission(IsCustomer, user))

    def test_user_in_an_unknown_group_is_only_a_customer(self):
        user = self.make_customer('kitchen')
        Group.objects.create(name='Kitchen').user_set.add(user)
        self.assertTrue(self.has_permission(IsCustomer, user))
        self.assertFalse(self.has_permission(IsManager, user))


class ManagerRoleModelTests(BaseAPITestCase):
    def test_creating_a_manager_puts_them_in_the_manager_group(self):
        manager = ManagerUser.objects.create_user('boss', PASSWORD, email='boss@example.com')
        self.assertEqual(list(manager.groups.values_list('name', flat=True)), ['Manager'])
        self.assertIsInstance(manager, ManagerUser)

    def test_manager_password_is_hashed_and_usable(self):
        manager = self.make_manager()
        self.assertNotEqual(manager.password, PASSWORD)
        self.assertTrue(manager.check_password(PASSWORD))
        response = self.client_for().post(LOGIN, {'username': 'manager', 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_manager_list_only_holds_managers(self):
        self.make_customer('customer'), self.make_crew('crew')
        self.make_manager('boss')
        self.assertEqual(list(ManagerUser.objects.values_list('username', flat=True)), ['boss'])

    def test_invalid_managers_are_rejected_and_nothing_is_created(self):
        self.make_customer('taken')
        for label, kwargs in (
            ('weak password', {'username': 'weak', 'password': '123'}),
            ('blank password', {'username': 'blank', 'password': ''}),
            ('username of a customer', {'username': 'taken', 'password': PASSWORD}),
            ('bad email', {'username': 'mail', 'password': PASSWORD, 'email': 'nope'}),
            ('empty username', {'username': '', 'password': PASSWORD}),
        ):
            with self.subTest(label):
                before = User.objects.count()
                with self.assertRaises(ValidationError):
                    ManagerUser.objects.create_user(**kwargs)
                self.assertEqual(User.objects.count(), before)

    def test_a_password_is_required(self):
        with self.assertRaises(TypeError):
            ManagerUser.objects.create_user('nopassword')

    def test_no_half_created_manager_when_the_group_is_missing(self):
        Group.objects.filter(name='Manager').delete()
        with self.assertRaises(Group.DoesNotExist):
            ManagerUser.objects.create_user('orphan', PASSWORD)
        self.assertFalse(User.objects.filter(username='orphan').exists())


class ManagerListEndpointTests(BaseAPITestCase):
    def test_a_manager_can_list_managers(self):
        self.make_manager('boss'), self.make_manager('boss2'), self.make_customer(), self.make_crew()
        response = self.client_for(User.objects.get(username='boss')).get(MANAGERS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(user['username'] for user in response.data), ['boss', 'boss2'])

    def test_only_managers_can_list_managers(self):
        for user, expected in ((None, 401), (self.make_customer(), 403), (self.make_crew(), 403)):
            with self.subTest(user=user):
                self.assertEqual(self.client_for(user).get(MANAGERS).status_code, expected)

    def test_managers_cannot_be_added_or_removed_through_the_api(self):
        manager, customer = self.make_manager(), self.make_customer()
        client = self.client_for(manager)
        self.assertEqual(client.post(MANAGERS, {'username': customer.username}, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(client.delete(f'{MANAGERS}/{manager.id}').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(list(customer.groups.all()), [])
        self.assertTrue(ManagerUser.objects.filter(pk=manager.pk).exists())


class CreateUserCommandTests(BaseAPITestCase):
    def run_command(self, password=PASSWORD, **options):
        with mock.patch.dict(os.environ, {'DJANGO_USER_PASSWORD': password}):
            call_command('create_user', stdout=StringIO(), **options)

    def groups_of(self, username):
        return list(User.objects.get(username=username).groups.values_list('name', flat=True))

    def test_creates_a_manager(self):
        self.run_command(role='manager', username='boss', email='boss@example.com')
        self.assertEqual(self.groups_of('boss'), ['Manager'])

    def test_creates_a_delivery_crew_member(self):
        self.run_command(role='crew', username='driver')
        self.assertEqual(self.groups_of('driver'), ['Delivery Crew'])

    def test_creates_a_customer_without_a_role(self):
        self.run_command(role='customer', username='alice')
        self.assertEqual(self.groups_of('alice'), [])
        self.assertTrue(User.objects.get(username='alice').check_password(PASSWORD))

    def test_bad_input_is_a_command_error_and_creates_nothing(self):
        self.make_customer('taken')
        for label, kwargs in (
            ('weak password', {'password': '123', 'role': 'crew', 'username': 'weak'}),
            ('taken username', {'role': 'customer', 'username': 'taken'}),
            ('bad email', {'role': 'manager', 'username': 'mail', 'email': 'nope'}),
        ):
            with self.subTest(label):
                before = User.objects.count()
                with self.assertRaises(CommandError):
                    self.run_command(**kwargs)
                self.assertEqual(User.objects.count(), before)

    def test_the_password_can_be_typed_at_a_prompt(self):
        with mock.patch.dict(os.environ, clear=False), mock.patch('restaurant.management.commands.create_user.getpass', side_effect=[PASSWORD, PASSWORD]):
            os.environ.pop('DJANGO_USER_PASSWORD', None)
            call_command('create_user', role='customer', username='prompted', stdout=StringIO())
        self.assertTrue(User.objects.filter(username='prompted').exists())

    def test_mismatching_passwords_at_the_prompt_create_nothing(self):
        with mock.patch.dict(os.environ, clear=False), mock.patch('restaurant.management.commands.create_user.getpass', side_effect=[PASSWORD, 'different']):
            os.environ.pop('DJANGO_USER_PASSWORD', None)
            with self.assertRaises(CommandError):
                call_command('create_user', role='customer', username='mismatch', stdout=StringIO())
        self.assertFalse(User.objects.filter(username='mismatch').exists())
