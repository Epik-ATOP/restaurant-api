from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import MenuItem, Order
from .serializers import MenuItemSerializer, OrderSerializer
from .permissions import IsStaff, IsOwnerOrStaff

# Create your views here.
class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filterset_fields = ['category']


    def get_permissions(self):
        if self.action in ['list','retrieve']:
            return [AllowAny()]
        return [IsStaff()]

class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get','post','patch','head','options']
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action == 'retrieve':
            return [IsAuthenticated(), IsOwnerOrStaff()]
        return [IsStaff()]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)