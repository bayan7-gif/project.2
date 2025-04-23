from django.test import TestCase, Client
from .models import Order
from .forms import OrderForm
from django.urls import reverse
from decimal import Decimal


class OrderTests(TestCase):
    """Набор тестов для проверки функционала заказов."""

    def setUp(self):
        """Инициализация тестовых данных."""
        self.client = Client()
        Order.objects.create(
            table_number=1,
            items=[{'name': 'Coffee', 'price': 2.5}],
            total_price=2.5,
            status='pending',
        )

    def test_order_creation(self):
        """Проверка корректного создания заказа."""
        order = Order.objects.get(table_number=1)
        self.assertEqual(order.status, 'pending')

    def test_order_status_update(self):
        """Проверка обновления статуса заказа."""
        order = Order.objects.get(table_number=1)
        url = reverse('update_order', args=[order.id])
        response = self.client.post(
            url,
            {
                'table_number': 1,
                'status': 'ready',
                'items_text': 'Coffee - 2.5',
            },
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'ready')

    def test_revenue_calculation(self):
        """Проверка подсчета общей выручки."""
        Order.objects.create(
            table_number=2,
            items=[{'name': 'Tea', 'price': 1.5}],
            total_price=1.5,
            status='paid',
        )
        Order.objects.create(
            table_number=3,
            items=[{'name': 'Cake', 'price': 2.5}],
            total_price=2.5,
            status='paid',
        )
        response = self.client.get(reverse('revenue_report'))
        self.assertContains(response, "4.00")

    def test_order_price_update(self):
        """Проверка обновления суммы заказа."""
        order = Order.objects.get(table_number=1)
        self.assertEqual(order.total_price, Decimal('2.50'))

        form_data = {
            'table_number': 1,
            'status': 'ready',
            'items_text': 'Coffee - 3.0\nCake - 2.0',
        }
        form = OrderForm(instance=order, data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        updated_order = form.save()
        self.assertEqual(updated_order.total_price, Decimal('5.00'))

    def test_decimal_serialization(self):
        """Проверка корректной сериализации Decimal значений."""
        form_data = {
            'table_number': 1,
            'status': 'pending',
            'items_text': 'Пицца - 133.03',
        }
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        order = form.save()
        self.assertIsInstance(order.items[0]['price'], float)
        self.assertEqual(order.items[0]['price'], 133.03)
        self.assertEqual(order.total_price, Decimal('133.03'))