# rutas/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from config.choices import EstadoGeneral
from envios.querysets import RutaQuerySet


class Ruta(models.Model):
    codigo = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9-]+$',
                message='El codigo solo debe contener mayusculas, numeros o guiones.'
            )
        ]
    )
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    dias_entrega = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    estado = models.IntegerField(
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO
    )

    objects = RutaQuerySet.as_manager()

    def __str__(self):
        return f'{self.codigo}: {self.origen} -> {self.destino}'

    def clean(self):
        super().clean()
        if self.origen and self.destino and self.origen.strip().lower() == self.destino.strip().lower():
            raise ValidationError({'destino': 'El origen y destino no pueden ser iguales.'})

    class Meta:
        db_table = 'rutas'
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'
        ordering = ['origen', 'destino']

