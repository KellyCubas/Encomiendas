from rest_framework import permissions

from envios.models import Empleado


class EsEmpleadoActivo(permissions.BasePermission):
    message = 'Debe ser un empleado activo para realizar esta accion.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return Empleado.objects.activos().filter(email=request.user.email).exists()


class EsPropietarioOAdmin(permissions.BasePermission):
    message = 'Solo el propietario o un administrador puede acceder a este recurso.'

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        email = request.user.email
        return email in {obj.remitente.email, obj.destinatario.email}
