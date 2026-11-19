from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import MenuItem, Order
from .serializers import MenuItemSerializer, OrderSerializer
from .permissions import IsStaff, IsOwnerOrStaff


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all().order_by('id')
    serializer_class = MenuItemSerializer
    filterset_fields = ['category']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsStaff()]


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.select_related('customer').prefetch_related(
        'items__menu_item'
    ).order_by('-created_at', '-id')
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action == 'retrieve':
            return [IsAuthenticated(), IsOwnerOrStaff()]
        return [IsStaff()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            return queryset.filter(customer=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)