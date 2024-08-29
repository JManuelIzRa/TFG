from django.test import TestCase, Client
from lpr_app.models import User
from django.middleware.csrf import get_token
from django.utils.html import escape
from django.db import connection
from django.urls import reverse
from django.contrib.auth import get_user_model



class SecurityTests(TestCase):
    
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    # SQL Injection
    def test_sql_injection(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", ['testuser'])
            result = cursor.fetchall()
            self.assertIsNotNone(result)

    def test_csrf_protection(self):
        # Hacer una solicitud GET inicial para obtener el token CSRF
        response = self.client.get(reverse('login'))
        csrf_token = response.cookies.get('csrftoken')
        
        self.assertIsNotNone(csrf_token, "CSRF token not found in the cookies")
        
        # Hacer una solicitud POST usando el token CSRF obtenido
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password',
            'csrfmiddlewaretoken': csrf_token.value
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_post_request_without_csrf(self):
        # Realizar una solicitud POST sin incluir el token CSRF
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password'
        }, follow=True)
        # Verificar que la respuesta tiene el código de estado 403
        self.assertEqual(response.status_code, 403, "Request without CSRF token should be forbidden")

    def test_post_request_with_invalid_csrf(self):
        # Obtener un token CSRF válido inicialmente
        response = self.client.get(reverse('login'))
        csrf_token = response.cookies.get('csrftoken')

        # Modificar el token CSRF para que sea incorrecto
        invalid_csrf_token = 'invalidtoken'

        # Realizar una solicitud POST con el token CSRF incorrecto
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password',
            'csrfmiddlewaretoken': invalid_csrf_token
        }, follow=True)
        # Verificar que la respuesta tiene el código de estado 403
        self.assertEqual(response.status_code, 403, "Request with invalid CSRF token should be forbidden")


    def test_login_required(self):
        response = self.client.get('/license_plate/')
        self.assertEqual(response.status_code, 302)  # Redirecciona al login

    def test_user_permissions(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.login(username='testuser', password='password')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 403)  # Prohibido

class XSSProtectionTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

    def test_xss_protection_on_all_views(self):
        # Lista de todas las vistas a probar
        urls_to_test = [
            reverse('home'),  # Asume que tienes una vista de inicio
            reverse('login'),
            reverse('logout'),
            reverse('change-password'),
            reverse('license_plate:license_plate'),  # Asume que tienes una vista de login
            # Añadir aquí las URLs de todas tus vistas
        ]

        xss_string = "<script>alert('XSS');</script>"

        for url in urls_to_test:
            with self.subTest(url=url):
                response = self.client.get(url, {'comment': xss_string})
                self.assertNotContains(response, "<script>alert('XSS');</script>", html=True)