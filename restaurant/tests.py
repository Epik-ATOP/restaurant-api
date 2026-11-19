from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import MenuItem, Order, OrderItem


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class RestaurantAPITests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username='customer',
            password='test-password',
        )
        self.other_customer = user_model.objects.create_user(
            username='other-customer',
            password='test-password',
        )
        self.staff = user_model.objects.create_user(
            username='staff',
            password='test-password',
            is_staff=True,
        )
        self.menu_item = MenuItem.objects.create(
            name='Soup',
            description='Daily soup',
            price=Decimal('5.50'),
            category='appetizers',
        )
        self.second_menu_item = MenuItem.objects.create(
            name='Cake',
            description='Chocolate cake',
            price=Decimal('4.25'),
            category='desserts',
        )
        self.client = APIClient()

    def create_order(self, customer=None, status='pending'):
        order = Order.objects.create(
            customer=customer or self.customer,
            table_number=1,
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=1,
        )
        return order

    def test_menu_is_public_filtered_and_staff_managed(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/menu/', {'category': 'appetizers'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Soup')

        payload = {
            'name': 'Salad',
            'description': 'Green salad',
            'price': '8.00',
            'category': 'mains',
            'is_available': False,
        }
        self.assertEqual(
            self.client.post('/api/menu/', payload, format='json').status_code,
            401,
        )

        self.client.force_authenticate(user=self.customer)
        self.assertEqual(
            self.client.post('/api/menu/', payload, format='json').status_code,
            403,
        )

        self.client.force_authenticate(user=self.staff)
        response = self.client.post('/api/menu/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['is_available'])

        response = self.client.patch(
            f"/api/menu/{response.data['id']}/",
            {'is_available': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_available'])

    def test_customer_can_create_order_with_multiple_items_and_server_total(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            '/api/orders/',
            {
                'table_number': 3,
                'items': [
                    {'menu_item': self.menu_item.id, 'quantity': 2},
                    {'menu_item': self.second_menu_item.id, 'quantity': 1},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['total'], Decimal('15.25'))
        self.assertEqual(len(response.data['items']), 2)
        self.assertEqual(
            response.data['items'][0]['line_total'],
            Decimal('11.00'),
        )
        self.assertEqual(
            OrderItem.objects.filter(order_id=response.data['id']).count(),
            2,
        )

    def test_order_requires_items_and_rejects_unavailable_menu_item(self):
        self.client.force_authenticate(user=self.customer)
        empty_response = self.client.post(
            '/api/orders/',
            {'table_number': 3, 'items': []},
            format='json',
        )
        self.assertEqual(empty_response.status_code, 400)

        self.menu_item.is_available = False
        self.menu_item.save(update_fields=['is_available'])
        unavailable_response = self.client.post(
            '/api/orders/',
            {
                'table_number': 3,
                'items': [{'menu_item': self.menu_item.id, 'quantity': 1}],
            },
            format='json',
        )
        self.assertEqual(unavailable_response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_access_and_staff_status_workflow(self):
        order = self.create_order()
        other_order = self.create_order(customer=self.other_customer)

        self.client.force_authenticate(user=self.customer)
        self.assertEqual(
            self.client.get(f'/api/orders/{order.id}/').status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f'/api/orders/{other_order.id}/').status_code,
            404,
        )
        self.assertEqual(
            self.client.get('/api/orders/').status_code,
            403,
        )

        self.client.force_authenticate(user=self.staff)
        self.assertEqual(self.client.get('/api/orders/').status_code, 200)
        skipped_status = self.client.patch(
            f'/api/orders/{order.id}/',
            {'status': 'ready'},
            format='json',
        )
        self.assertEqual(skipped_status.status_code, 400)

        for status in ('preparing', 'ready', 'served'):
            response = self.client.patch(
                f'/api/orders/{order.id}/',
                {'status': status},
                format='json',
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['status'], status)

        backwards_status = self.client.patch(
            f'/api/orders/{order.id}/',
            {'status': 'preparing'},
            format='json',
        )
        self.assertEqual(backwards_status.status_code, 400)

    def test_order_list_filters_by_status_and_is_paginated(self):
        for _ in range(11):
            self.create_order()
        self.create_order(status='ready')

        self.client.force_authenticate(user=self.staff)
        response = self.client.get('/api/orders/', {'status': 'ready'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 10)
