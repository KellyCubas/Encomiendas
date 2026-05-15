from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from config.choices import EstadoGeneral, TipoDocumento
from envios.querysets import ClienteQuerySet


class Cliente(models.Model):
    tipo_doc = models.CharField(
        max_length=3,
        choices=TipoDocumento.choices,
        default=TipoDocumento.DNI
    )
    nro_doc = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9A-Za-z]+$',
                message='El numero de documento solo debe contener letras y numeros.'
            )
        ]
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9+\-\s]+$',
                message='El telefono solo debe contener numeros, espacios, + o -.'
            )
        ]
    )
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    estado = models.IntegerField(
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    objects = ClienteQuerySet.as_manager()

    def __str__(self):
        return f'{self.nro_doc} - {self.apellidos}, {self.nombres}'

    @property
    def nombre_completo(self):
        return f'{self.apellidos}, {self.nombres}'

    @property
    def esta_activo(self):
        return self.estado == EstadoGeneral.ACTIVO

    @property
    def total_encomiendas_enviadas(self):
        return self.envios_como_remitente.count()

    def clean(self):
        super().clean()
        if self.tipo_doc == TipoDocumento.DNI and len(self.nro_doc) != 8:
            raise ValidationError({'nro_doc': 'El DNI debe tener 8 digitos.'})
        if self.tipo_doc == TipoDocumento.RUC and len(self.nro_doc) != 11:
            raise ValidationError({'nro_doc': 'El RUC debe tener 11 digitos.'})
        if self.tipo_doc == TipoDocumento.PASAPORTE and len(self.nro_doc) < 6:
            raise ValidationError({'nro_doc': 'El pasaporte debe tener al menos 6 caracteres.'})

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['apellidos', 'nombres']
