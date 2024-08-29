from django.test import SimpleTestCase, TestCase, Client
import datetime
from django.urls import reverse, resolve
from lpr_app.models import User
from license_plate.models import LicensePlate
from django.contrib.auth import get_user_model
from .views import HomeView, LoginFormView
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm



class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            firstname="John",
            secondname="Doe",
            username="johndoe",
            password="password",
            email="johndoe@example.com"
        )
    
    # UNIT DONE
    def test_user_creation(self):
        self.assertEqual(self.user.firstname, "John")
        self.assertEqual(self.user.secondname, "Doe")
        self.assertEqual(self.user.username, "johndoe")
        self.assertEqual(self.user.email, "johndoe@example.com")
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_admin)
        self.assertTrue(self.user.is_staff)
    
    # UNIT DONE
    def test_get_full_name(self):
        full_name = self.user.get_full_name()
        self.assertEqual(full_name, "John Doe")
    
    # UNIT DONE
    def test_user_soft_delete(self):
        self.user.delete()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_admin)
        self.assertTrue(self.user.deleted)
        self.assertIn("(deleted", self.user.username)


class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        today = datetime.date.today()
        LicensePlate.objects.create(entry_date=today, amount_paid=10)
        LicensePlate.objects.create(entry_date=today, amount_paid=20)

        LicensePlate.objects.create(entry_date=today, exit_date=today, amount_paid=10)
        LicensePlate.objects.create(entry_date=today, exit_date=today, amount_paid=20)
    
    # Integration Test DONE
    def test_home_view_context_data(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['plates_today_count'], '4')
        self.assertEqual(response.context['real_vehicles'], '2')
        self.assertEqual(response.context['today_gains'], '30.00')
        self.assertIn('labels', response.context)
        self.assertIn('data', response.context)


class LoginFormViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')

    # Functional
    def test_login_form_view_template(self):
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, 'login.html')

    # Integration DONE
    def test_login_form_view_valid_post(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': '12345'})
        self.assertEqual(response.status_code, 302)  # Redirects to success_url

    # Integration DONE
    def test_login_form_view_invalid_post(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)  # Should stay on the same page
        form = response.context['form']
        self.assertIsInstance(form, AuthenticationForm)
        self.assertTrue(form.errors)
        self.assertFormError(response, 'form', None, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')

    # Unit DONE
    def assertFormError(self, response, form_name, field, errors):
        form = response.context[form_name]
        if field is None:
            # Non-field errors
            field_errors = form.non_field_errors()
        else:
            field_errors = form.errors[field]
        self.assertIn(errors, field_errors)


class UrlTests(SimpleTestCase):
    # Functional DONE
    def test_home_url_resolves(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func.view_class, HomeView)

    # Functional DONE
    def test_login_url_resolves(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class, LoginFormView)
    
    # Functional DONE
    def test_logout_url_resolves(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func.view_class, auth_views.LogoutView)
    
    # Functional DONE
    def test_change_password_url_resolves(self):
        url = reverse('change-password')
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordChangeView)

class UrlAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

    # Functional DONE
    def test_home_url_access(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    # Functional DONE

    def test_login_url_access(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    # Functional DONE

    def test_logout_url_access(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirects after logout
    # Functional DONE

    def test_change_password_url_access(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('change-password'))
        self.assertEqual(response.status_code, 200)