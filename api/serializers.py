from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from clientes.models import Cliente
from config.choices import EstadoEnvio
from envios.models import Empleado, Encomienda, HistorialEstado
from rutas.models import Ruta


class ClienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    esta_activo = serializers.BooleanField(read_only=True)
    total_encomiendas_enviadas = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'tipo_doc', 'nro_doc', 'nombres', 'apellidos',
            'nombre_completo', 'telefono', 'email', 'esta_activo',
            'total_encomiendas_enviadas',
        ]


class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = [
            'id', 'codigo', 'origen', 'destino', 'precio_base',
            'dias_entrega', 'estado',
        ]


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ['id', 'codigo', 'nombres', 'apellidos', 'cargo', 'email', 'estado']


class HistorialEstadoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.SerializerMethodField()
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display = serializers.CharField(source='get_estado_nuevo_display', read_only=True)

    class Meta:
        model = HistorialEstado
        fields = [
            'id', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display', 'empleado_nombre',
            'observacion', 'fecha_cambio',
        ]

    def get_empleado_nombre(self, obj) -> str:
        return str(obj.empleado)


class EncomiendaBulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        return [self.child.create(item) for item in validated_data]


class EncomiendaSerializer(serializers.ModelSerializer):
    esta_entregada = serializers.BooleanField(read_only=True)
    tiene_retraso = serializers.BooleanField(read_only=True)
    dias_en_transito = serializers.IntegerField(read_only=True)
    descripcion_corta = serializers.CharField(read_only=True)
    estado_display = serializers.SerializerMethodField()
    remitente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(), write_only=True, source='ruta'
    )

    class Meta:
        model = Encomienda
        list_serializer_class = EncomiendaBulkListSerializer
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta',
            'peso_kg', 'volumen_cm3', 'costo_envio',
            'remitente', 'destinatario', 'ruta', 'empleado_registro',
            'remitente_id', 'destinatario_id', 'ruta_id',
            'estado', 'estado_display', 'fecha_registro',
            'fecha_entrega_est', 'fecha_entrega_real',
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
            'observaciones',
        ]
        read_only_fields = [
            'id', 'remitente', 'destinatario', 'ruta', 'empleado_registro',
            'fecha_registro', 'fecha_entrega_real',
        ]

    def get_estado_display(self, obj) -> str:
        return obj.get_estado_display()

    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0.')
        return value

    def validate_codigo(self, value):
        value = value.strip().upper()
        if not value.startswith('ENC-'):
            raise serializers.ValidationError('El codigo debe iniciar con ENC-.')
        if self.instance is None and Encomienda.objects.filter(codigo=value).exists():
            raise serializers.ValidationError('Ya existe una encomienda con este codigo.')
        return value

    def validate(self, attrs):
        remitente = attrs.get('remitente', getattr(self.instance, 'remitente', None))
        destinatario = attrs.get('destinatario', getattr(self.instance, 'destinatario', None))
        if remitente and destinatario and remitente == destinatario:
            raise serializers.ValidationError({
                'destinatario_id': 'El destinatario no puede ser el mismo que el remitente.'
            })
        fecha_entrega_est = attrs.get(
            'fecha_entrega_est',
            getattr(self.instance, 'fecha_entrega_est', None),
        )
        if fecha_entrega_est and fecha_entrega_est < timezone.now().date():
            raise serializers.ValidationError({
                'fecha_entrega_est': 'La fecha de entrega estimada no puede ser en el pasado.'
            })
        return attrs

    def to_internal_value(self, data):
        data = data.copy()
        if data.get('codigo'):
            data['codigo'] = data['codigo'].strip().upper()
        if data.get('descripcion'):
            data['descripcion'] = data['descripcion'].strip()
        if data.get('costo_envio'):
            try:
                data['costo_envio'] = f"{Decimal(str(data['costo_envio'])):.2f}"
            except Exception as exc:
                raise serializers.ValidationError({
                    'costo_envio': 'Debe enviar un costo valido.'
                }) from exc
        return super().to_internal_value(data)

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['ruta_codigo'] = instance.ruta.codigo
        data['ruta_origen'] = instance.ruta.origen
        data['ruta_destino'] = instance.ruta.destino
        data['costo_display'] = f"S/ {instance.costo_envio:.2f}"
        data['estado_color'] = {
            EstadoEnvio.PENDIENTE: 'gray',
            EstadoEnvio.EN_TRANSITO: 'blue',
            EstadoEnvio.EN_DESTINO: 'orange',
            EstadoEnvio.ENTREGADO: 'green',
            EstadoEnvio.DEVUELTO: 'red',
        }.get(instance.estado, 'gray')

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not (user.is_staff or user.is_superuser):
            data.pop('observaciones', None)
            data.pop('empleado_registro', None)
        return data


class EncomiendaListSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.CharField(source='remitente.nombre_completo', read_only=True)
    destinatario_nombre = serializers.CharField(source='destinatario.nombre_completo', read_only=True)
    ruta_destino = serializers.CharField(source='ruta.destino', read_only=True)
    estado_display = serializers.SerializerMethodField()
    tiene_retraso = serializers.BooleanField(read_only=True)

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'estado', 'estado_display',
            'remitente_nombre', 'destinatario_nombre', 'ruta_destino',
            'peso_kg', 'costo_envio', 'fecha_registro',
            'fecha_entrega_est', 'tiene_retraso',
        ]

    def get_estado_display(self, obj) -> str:
        return obj.get_estado_display()


class EncomiendaDetailSerializer(EncomiendaSerializer):
    remitente = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta = RutaSerializer(read_only=True)
    empleado_registro = EmpleadoSerializer(read_only=True)
    historial = HistorialEstadoSerializer(many=True, read_only=True)

    class Meta(EncomiendaSerializer.Meta):
        fields = EncomiendaSerializer.Meta.fields + ['historial']


class EncomiendaV2Serializer(EncomiendaListSerializer):
    links = serializers.SerializerMethodField()

    class Meta(EncomiendaListSerializer.Meta):
        fields = EncomiendaListSerializer.Meta.fields + ['links']

    @extend_schema_field(dict)
    def get_links(self, obj):
        request = self.context.get('request')
        url = request.build_absolute_uri(f'/api/v2/encomiendas/{obj.pk}/') if request else ''
        return {'self': url}
