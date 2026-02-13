from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, MenuItem


class MenuItemsAPITests(APITestCase):
    def setUp(self):
        category = Category.objects.create(slug="mains", title="Mains")
        MenuItem.objects.create(
            title="Greek Salad",
            price="12.50",
            featured=True,
            category=category,
        )

    def test_public_can_list_menu_items(self):
        response = self.client.get("/api/menu-items/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
