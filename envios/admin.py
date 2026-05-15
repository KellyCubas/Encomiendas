from django.contrib import admin
from .models import Empleado, Encomienda, HistorialEstado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'apellidos', 'nombres', 'cargo', 'email', 'estado')
    list_filter = ('cargo', 'estado')
    search_fields = ('codigo', 'nombres', 'apellidos', 'email')
    ordering = ('apellidos', 'nombres')


@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'remitente', 'destinatario', 'ruta', 'estado', 'costo_envio', 'fecha_registro')
    list_filter = ('estado', 'ruta', 'fecha_registro')
    search_fields = (
        'codigo',
        'descripcion',
        'remitente__nro_doc',
        'remitente__nombres',
        'remitente__apellidos',
        'destinatario__nro_doc',
        'destinatario__nombres',
        'destinatario__apellidos',
    )
    date_hierarchy = 'fecha_registro'
    ordering = ('-fecha_registro',)


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio')
    list_filter = ('estado_anterior', 'estado_nuevo', 'fecha_cambio')
    search_fields = ('encomienda__codigo', 'empleado__codigo', 'empleado__nombres', 'empleado__apellidos')
    date_hierarchy = 'fecha_cambio'
