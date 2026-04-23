from django.contrib import admin
from .models import Encomienda

@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'peso_kg', 'estado')