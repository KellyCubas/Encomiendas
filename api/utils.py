from rest_framework.exceptions import ValidationError

from envios.models import Empleado


def get_empleado_for_user(user):
    empleado = Empleado.objects.activos().filter(email=user.email).first()
    if empleado:
        return empleado
    if user.is_staff or user.is_superuser:
        empleado = Empleado.objects.activos().first()
        if empleado:
            return empleado
    raise ValidationError({'empleado': 'El usuario autenticado no tiene empleado activo asociado.'})
