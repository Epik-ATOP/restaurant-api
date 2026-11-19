from django.db import transaction
from rest_framework import serializers
from .models import MenuItem, Order, OrderItem


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'is_available']


class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='menu_item.name', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=8, decimal_places=2,
        source='menu_item.price', read_only=True
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['menu_item', 'name', 'quantity', 'unit_price', 'line_total']

    def get_line_total(self, obj):
        return obj.menu_item.price * obj.quantity


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, allow_empty=False)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'table_number', 'status', 'items', 'total', 'created_at']
        read_only_fields = ['created_at']

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is None:
            fields['status'].read_only = True
        else:
            fields['items'].read_only = True
        return fields

    def get_total(self, obj):
        return sum(
            (item.menu_item.price * item.quantity for item in obj.items.all()),
            start=0,
        )

    def validate_items(self, items):
        errors = []
        for item in items:
            menu_item = item['menu_item']
            if not menu_item.is_available:
                errors.append({
                    'menu_item': menu_item.id,
                    'error': f'{menu_item.name} is currently unavailable.',
                })

        if errors:
            raise serializers.ValidationError(errors)
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                menu_item=item_data['menu_item'],
                quantity=item_data['quantity'],
            )
        return order

    def validate_status(self, new_status):
        flow = [status for status, _ in Order.STATUS_CHOICES]
        current = self.instance.status

        if flow.index(new_status) != flow.index(current) + 1:
            raise serializers.ValidationError(
                f"Status can only advance one step from '{current}'."
            )
        return new_status