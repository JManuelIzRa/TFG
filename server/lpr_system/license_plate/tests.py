from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from .models import LicensePlate
from lpr_app.models import User
from datetime import timedelta, datetime, time, date

class LicensePlateTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.client = Client()
        
        # Create a test user and log them in
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        now = datetime.now()
        entry_time = (now - timedelta(minutes=20)).time()

        self.plate = LicensePlate.objects.create(
            plate_number="ABC123",
            entry_date=date.today(),
            entry_time=entry_time,
        )

    def test_license_plate_list_view(self):
        response = self.client.get(reverse('license_plate:license_plate'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'records/index.html')

    def test_register_plate(self):
        url = reverse('license_plate:api_register_plate')
        data = {'plate_number': 'XYZ789'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LicensePlate.objects.count(), 2)
        self.assertEqual(LicensePlate.objects.get(plate_number='XYZ789').plate_number, 'XYZ789')

    def test_register_plate_invalid_data(self):
        url = reverse('license_plate:api_register_plate')
        data = {'plate_number': ''}  # Invalid data: plate_number is required
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_exit(self):
        url = reverse('license_plate:register_exit')
        data = {'plate_number': 'ABC123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.plate.refresh_from_db()
        self.assertIsNotNone(self.plate.exit_date)
        self.assertIsNotNone(self.plate.exit_time)
        self.assertGreater(self.plate.amount_paid, 0.0)

    def test_register_exit_no_entry_record(self):
        url = reverse('license_plate:register_exit')
        data = {'plate_number': 'XYZ789'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No entry record found for this plate number.')

    def test_register_exit_invalid_data(self):
        url = reverse('license_plate:register_exit')
        data = {'plate_number': ''}  # Invalid data: plate_number is required
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_plate_already_exists(self):
        url = reverse('license_plate:api_register_plate')
        data = {'plate_number': 'ABC123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'A plate with this number already exists and is in the parking at that moment.')

    def test_delete_license_plate(self):
        url = reverse('license_plate:delete_license_plate', args=[self.plate.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(LicensePlate.objects.filter(id=self.plate.id).exists())

    def test_delete_license_plate_get_request(self):
        url = reverse('license_plate:delete_license_plate', args=[self.plate.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_license_plate_list_pagination(self):
        # Create more LicensePlate objects to trigger pagination
        for i in range(15):
            LicensePlate.objects.create(
                plate_number=f"TEST{i}",
                entry_date=date.today(),
                entry_time=datetime.now().time()
            )
        response = self.client.get(reverse('license_plate:license_plate'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'])

    def test_license_plate_list_filtering(self):
        LicensePlate.objects.create(
            plate_number="XYZ789",
            entry_date=date.today() - timedelta(days=1),
            entry_time=datetime.now().time()
        )
        response = self.client.get(reverse('license_plate:license_plate'), {'plate_number': 'XYZ789'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].plate_number, 'XYZ789')

    def test_license_plate_list_filtering_date(self):
        
        response = self.client.get(reverse('license_plate:license_plate'), {'filter': 'day'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].plate_number, 'ABC123')

    def test_license_plate_list_filtering_no_results(self):
        response = self.client.get(reverse('license_plate:license_plate'), {'plate_number': 'NONEXISTENT'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)
