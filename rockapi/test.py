from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework import status


class SanityTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_math_still_works(self):
        self.assertEqual(2 + 2, 4)

    def test_uppercase(self):
        self.assertEqual("rock".upper(), "ROCK")

    def test_api_mock(self):
        # This won't hit a real view, but it shows test usage
        response = self.client.get('/fake-url')
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK])