from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import ClienteViewSet, EncomiendaV2ViewSet, RutaViewSet

router = DefaultRouter()
router.register('clientes', ClienteViewSet, basename='cliente-v2')
router.register('rutas', RutaViewSet, basename='ruta-v2')
router.register('encomiendas', EncomiendaV2ViewSet, basename='encomienda-v2')

urlpatterns = [
    path('', include(router.urls)),
]
