from rest_framework.permissions import BasePermission

class IsStaff(BasePermission):
    message = 'u gotta be staff'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsOwnerOrStaff(BasePermission):
    message = 'u can only view YOUR owners'

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.customer == request.user