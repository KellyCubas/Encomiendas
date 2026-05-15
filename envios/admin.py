from django.contrib import admin
from django.utils.html import format_html
from .models import Empleado, Encomienda, HistorialEstado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'apellidos', 'nombres', 'cargo', 'email', 'estado')
    list_filter = ('cargo', 'estado')
    search_fields = ('codigo', 'nombres', 'apellidos', 'email')
    ordering = ('apellidos', 'nombres')


@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'remitente_nombre', 'destinatario_nombre',
        'ruta', 'estado_badge', 'peso_kg', 'fecha_registro'
    )
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
    readonly_fields = ('fecha_registro', 'fecha_entrega_real')
    date_hierarchy = 'fecha_registro'
    ordering = ('-fecha_registro',)
    list_per_page = 20
    fieldsets = (
        ('Identificacion', {
            'fields': ('codigo', 'descripcion', 'peso_kg', 'volumen_cm3')
        }),
        ('Partes', {
            'fields': ('remitente', 'destinatario', 'ruta', 'empleado_registro')
        }),
        ('Estado y fechas', {
            'fields': ('estado', 'costo_envio', 'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real')
        }),
        ('Notas', {
            'classes': ('collapse',),
            'fields': ('observaciones',)
        }),
    )

    def remitente_nombre(self, obj):
        return obj.remitente.nombre_completo
    remitente_nombre.short_description = 'Remitente'

    def destinatario_nombre(self, obj):
        return obj.destinatario.nombre_completo
    destinatario_nombre.short_description = 'Destinatario'

    def estado_badge(self, obj):
        colores = {
            'PE': '#6c757d',
            'TR': '#0d6efd',
            'DE': '#fd7e14',
            'EN': '#198754',
            'DV': '#dc3545',
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append('codigo')
        return readonly


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio')
    readonly_fields = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio')
    list_filter = ('estado_anterior', 'estado_nuevo', 'fecha_cambio')
    search_fields = ('encomienda__codigo', 'empleado__codigo', 'empleado__nombres', 'empleado__apellidos')
    date_hierarchy = 'fecha_cambio'
    ordering = ('-fecha_cambio',)
