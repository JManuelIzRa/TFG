from django.test import TestCase, Client
from django.urls import reverse
from lpr_app.models import User
from django.contrib.auth import get_user_model

class UserListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword', is_admin=True)
        self.client.login(username='testuser', password='testpassword')

        self.user1 = User.objects.create(username='client1', firstname='John', secondname='Doe', is_admin=False, email='john@example.com')
        self.user2 = User.objects.create(username='client2', firstname='Jane', secondname='Doe', is_admin=False, email='jane@example.com')
        self.user3 = User.objects.create(username='admin1', firstname='Admin', secondname='User', is_admin=True, email='admin@example.com')

    def test_user_list_filter_by_admin(self):
        response = self.client.get(reverse('users:users') + '?user=admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user3, response.context['object_list'])
        self.assertNotIn(self.user1, response.context['object_list'])
        self.assertNotIn(self.user2, response.context['object_list'])

    def test_user_list_filter_by_client(self):
        response = self.client.get(reverse('users:users') + '?user=client')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user1, response.context['object_list'])
        self.assertIn(self.user2, response.context['object_list'])
        self.assertNotIn(self.user3, response.context['object_list'])

    def test_user_list_filter_by_firstname(self):
        response = self.client.get(reverse('users:users') + '?firstname=John')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user1, response.context['object_list'])
        self.assertNotIn(self.user2, response.context['object_list'])

    def test_user_list_filter_by_secondname(self):
        response = self.client.get(reverse('users:users') + '?secondname=Doe')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user1, response.context['object_list'])
        self.assertIn(self.user2, response.context['object_list'])

    def test_user_list_filter_by_username(self):
        response = self.client.get(reverse('users:users') + '?username=client1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user1, response.context['object_list'])
        self.assertNotIn(self.user2, response.context['object_list'])
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import CreateAdminForm

class AdminCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(username='admin', password='adminpass', is_admin=True)
        self.client.login(username='admin', password='adminpass')

    def test_create_admin_success(self):
        url = reverse('users:add-user')
        data = {
            'firstname': 'New',
            'secondname': 'Admin',
            'username': 'newadmin',
            'password': 'newpassword',
            'repeat_password': 'newpassword',
            'email': 'newadmin@example.com',
            'is_admin': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='newadmin').exists())

    def test_create_admin_password_mismatch(self):
        url = reverse('users:add-user')
        data = {
            'firstname': 'New',
            'secondname': 'Admin',
            'username': 'newadmin',
            'password': 'newpassword',
            'repeat_password': 'differentpassword',
            'email': 'newadmin@example.com',
            'is_admin': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'repeat_password', 'Las contraseñas deben de ser idénticas')

class UserUpdateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(username='admin', password='adminpass', is_admin=True)
        self.client.login(username='admin', password='adminpass')
        self.user = User.objects.create(username='updateuser', firstname='Old', secondname='Name', is_admin=False)

    def test_update_user_success(self):
        url = reverse('users:edit-user', args=[self.user.pk])
        data = {
            'firstname': 'Updated',
            'secondname': 'Name',
            'email': 'updated@example.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.firstname, 'Updated')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_update_user_template(self):
        url = reverse('users:edit-user', args=[self.user.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'users/create_patient.html')

class DeletePersonViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(username='admin', password='adminpass', is_admin=True)
        self.client.login(username='admin', password='adminpass')
        self.user = User.objects.create(username='deleteuser', firstname='Delete', secondname='User')

    def test_delete_user_success(self):
        url = reverse('users:delete-person', args=[self.user.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "El usuario Delete User ha sido eliminado correctamente.")

class ClientCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(username='admin', password='adminpass', is_admin=True)
        self.client.login(username='admin', password='adminpass')

    def test_create_client_success(self):
        url = reverse('users:add-patient')
        data = {
            'firstname': 'Client',
            'secondname': 'User',
            'username': 'clientcode',
            'email': 'client@example.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='clientcode').exists())

    def test_create_client_duplicate_code(self):
        User.objects.create(username='duplicatecode', code='duplicatecode', firstname='Existing', secondname='Client', email='existing@example.com')
        url = reverse('users:add-patient')
        data = {
            'firstname': 'New',
            'secondname': 'Client',
            'username': 'duplicatecode',
            'email': 'newclient@example.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "El código introducido ya fue asignado a otra persona")

class DisablePersonTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(username='admin', password='adminpass', is_admin=True)
        self.client.login(username='admin', password='adminpass')
        self.user = User.objects.create(username='toggleduser', firstname='Toggle', secondname='User', is_active=True)

    def test_toggle_user_active_status(self):
        url = reverse('users:disable-person', args=[self.user.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
