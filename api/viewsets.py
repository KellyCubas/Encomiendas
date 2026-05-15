from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clientes.models import Cliente
from config.choices import EstadoEnvio
from envios.models import Encomienda
from rutas.models import Ruta

from .pagination import EncomiendaPagination
from .permissions import EsEmpleadoActivo, EsPropietarioOAdmin
from .serializers import (
    ClienteSerializer,
    EncomiendaDetailSerializer,
    EncomiendaListSerializer,
    EncomiendaSerializer,
    EncomiendaV2Serializer,
    RutaSerializer,
)
from .utils import get_empleado_for_user


class ClienteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['nombres', 'apellidos', 'nro_doc', 'email']
    ordering_fields = ['apellidos', 'nombres', 'fecha_registro']

    def get_queryset(self):
        qs = Cliente.objects.activos()
        termino = self.request.query_params.get('buscar')
        if termino:
            qs = qs.buscar(termino)
        return qs


class RutaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RutaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Ruta.objects.activas()
    search_fields = ['codigo', 'origen', 'destino']
    ordering_fields = ['origen', 'destino', 'precio_base']

    @method_decorator(cache_page(settings.CACHE_TTL))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EncomiendaViewSet(viewsets.ModelViewSet):
    queryset = Encomienda.objects.con_relaciones()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated, EsEmpleadoActivo, EsPropietarioOAdmin]
    pagination_class = EncomiendaPagination
    filterset_fields = ['estado', 'ruta', 'remitente', 'destinatario']
    search_fields = ['codigo', 'descripcion', 'remitente__apellidos', 'destinatario__apellidos']
    ordering_fields = ['fecha_registro', 'fecha_entrega_est', 'costo_envio', 'peso_kg']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        if self.action == 'list':
            return EncomiendaListSerializer
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        if self.action == 'v2_list':
            return EncomiendaV2Serializer
        return EncomiendaSerializer

    def get_queryset(self):
        qs = Encomienda.objects.con_relaciones()

        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        if self.request.query_params.get('con_retraso') in {'1', 'true', 'True'}:
            qs = qs.con_retraso()

        q = self.request.query_params.get('search')
        if q:
            qs = qs.filter(
                Q(codigo__icontains=q)
                | Q(descripcion__icontains=q)
                | Q(remitente__apellidos__icontains=q)
                | Q(destinatario__apellidos__icontains=q)
            )

        return qs

    def perform_create(self, serializer):
        serializer.save(empleado_registro=get_empleado_for_user(self.request.user))
        cache.delete(f'estadisticas_empleado_{self.request.user.id}')

    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f'estadisticas_empleado_{self.request.user.id}')

    @extend_schema(
        request=EncomiendaSerializer,
        examples=[
            OpenApiExample(
                'Cambio a transito',
                value={'estado': EstadoEnvio.EN_TRANSITO, 'observacion': 'Recogido en agencia'},
            )
        ],
    )
    @action(detail=True, methods=['post'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        encomienda = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response({'error': 'El campo estado es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            encomienda.cambiar_estado(
                nuevo_estado,
                get_empleado_for_user(request.user),
                observacion,
            )
        except (ValueError, DjangoValidationError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete_many([
            f'estadisticas_empleado_{request.user.id}',
            f'encomienda_detalle_{pk}',
        ])
        serializer = EncomiendaSerializer(encomienda, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        qs = Encomienda.objects.con_retraso().con_relaciones()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        qs = Encomienda.objects.pendientes().con_relaciones()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        cache_key = f'estadisticas_empleado_{request.user.id}'
        data = cache.get(cache_key)
        if data is None:
            data = {
                'activas': Encomienda.objects.activas().count(),
                'en_transito': Encomienda.objects.en_transito().count(),
                'con_retraso': Encomienda.objects.con_retraso().count(),
                'entregadas_mes': Encomienda.objects.filter(
                    estado=EstadoEnvio.ENTREGADO,
                    fecha_entrega_real__month=timezone.now().month,
                ).count(),
            }
            cache.set(cache_key, data, settings.CACHE_TTL)
        return Response(data)

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = EncomiendaSerializer(
            data=request.data,
            many=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        encomiendas = serializer.save(empleado_registro=get_empleado_for_user(request.user))
        cache.delete(f'estadisticas_empleado_{request.user.id}')
        output = EncomiendaSerializer(encomiendas, many=True, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='bulk_estado')
    def bulk_estado(self, request):
        ids = request.data.get('ids', [])
        nuevo_estado = request.data.get('estado')
        observacion = request.data.get('observacion', '')

        if not ids or not nuevo_estado:
            return Response(
                {'error': 'Debe enviar ids y estado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empleado = get_empleado_for_user(request.user)
        actualizadas = []
        errores = []
        existentes = set(Encomienda.objects.filter(id__in=ids).values_list('id', flat=True))
        no_encontrados = [pk for pk in ids if pk not in existentes]

        for encomienda in Encomienda.objects.filter(id__in=ids):
            try:
                encomienda.cambiar_estado(nuevo_estado, empleado, observacion)
                actualizadas.append(encomienda.id)
            except (ValueError, DjangoValidationError) as exc:
                errores.append({'id': encomienda.id, 'error': str(exc)})

        cache.delete(f'estadisticas_empleado_{request.user.id}')
        return Response({
            'actualizadas': actualizadas,
            'errores': errores,
            'no_encontrados': no_encontrados,
            'total': len(actualizadas),
        })


class EncomiendaV2ViewSet(EncomiendaViewSet):
    serializer_class = EncomiendaV2Serializer

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return EncomiendaV2Serializer
        return EncomiendaSerializer
