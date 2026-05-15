from datetime import timedelta

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from clientes.models import Cliente
from config.choices import EstadoEnvio, EstadoGeneral, TipoDocumento
from envios.models import Empleado, Encomienda
from rutas.models import Ruta


TEST_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'api-tests',
    }
}


@override_settings(CACHES=TEST_CACHE)
class EncomiendaAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            email='apiuser@example.com',
            password='ApiUser123',
            is_staff=True,
        )
        self.empleado = Empleado.objects.create(
            codigo='EMP-API',
            nombres='Ana',
            apellidos='Prueba',
            cargo='Operador',
            email='apiuser@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=timezone.now().date(),
        )
        self.remitente = Cliente.objects.create(
            tipo_doc=TipoDocumento.DNI,
            nro_doc='11111111',
            nombres='Luis',
            apellidos='Ramos',
            email='luis@example.com',
            estado=EstadoGeneral.ACTIVO,
        )
        self.destinatario = Cliente.objects.create(
            tipo_doc=TipoDocumento.DNI,
            nro_doc='22222222',
            nombres='Maria',
            apellidos='Soto',
            email='maria@example.com',
            estado=EstadoGeneral.ACTIVO,
        )
        self.ruta = Ruta.objects.create(
            codigo='LIM-CUS',
            origen='Lima',
            destino='Cusco',
            precio_base='25.00',
            dias_entrega=2,
            estado=EstadoGeneral.ACTIVO,
        )
        self.encomienda = Encomienda.objects.create(
            codigo='ENC-API-001',
            descripcion='Paquete de prueba',
            peso_kg='2.50',
            costo_envio='25.00',
            remitente=self.remitente,
            destinatario=self.destinatario,
            ruta=self.ruta,
            empleado_registro=self.empleado,
            fecha_entrega_est=timezone.now().date() + timedelta(days=2),
        )
        self.client.force_authenticate(self.user)

    def payload(self, codigo='ENC-API-002', destinatario=None):
        return {
            'codigo': codigo,
            'descripcion': 'Nueva encomienda desde API',
            'peso_kg': '3.00',
            'costo_envio': '30.00',
            'remitente_id': self.remitente.id,
            'destinatario_id': (destinatario or self.destinatario).id,
            'ruta_id': self.ruta.id,
            'fecha_entrega_est': str(timezone.now().date() + timedelta(days=2)),
        }

    def test_obtener_token_jwt(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/auth/token/', {
            'username': 'apiuser',
            'password': 'ApiUser123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_listar_encomiendas(self):
        response = self.client.get('/api/v1/encomiendas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_crear_encomienda(self):
        response = self.client.post('/api/v1/encomiendas/', self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Encomienda.objects.count(), 2)

    def test_crear_encomienda_error_400(self):
        response = self.client.post(
            '/api/v1/encomiendas/',
            self.payload(destinatario=self.remitente),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_estado(self):
        response = self.client.post(
            f'/api/v1/encomiendas/{self.encomienda.id}/cambiar_estado/',
            {'estado': EstadoEnvio.EN_TRANSITO, 'observacion': 'Sale de agencia'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.encomienda.refresh_from_db()
        self.assertEqual(self.encomienda.estado, EstadoEnvio.EN_TRANSITO)
        self.assertEqual(self.encomienda.historial.count(), 1)

    def test_acciones_personalizadas(self):
        pendientes = self.client.get('/api/v1/encomiendas/pendientes/')
        estadisticas = self.client.get('/api/v1/encomiendas/estadisticas/')
        self.assertEqual(pendientes.status_code, status.HTTP_200_OK)
        self.assertEqual(estadisticas.status_code, status.HTTP_200_OK)
        self.assertIn('activas', estadisticas.data)

    def test_versionado_v2(self):
        response = self.client.get('/api/v2/encomiendas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('links', response.data['results'][0])
