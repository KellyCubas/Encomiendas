from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .viewsets import ClienteViewSet, EncomiendaViewSet, RutaViewSet

router = DefaultRouter()
router.register('clientes', ClienteViewSet, basename='cliente')
router.register('rutas', RutaViewSet, basename='ruta')
router.register('encomiendas', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    path('auth/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema-v1'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema-v1'), name='swagger-ui-v1'),
    path('fbv/encomiendas/', views.encomienda_list_fbv, name='fbv-encomienda-list'),
    path('fbv/encomiendas/<int:pk>/', views.encomienda_detail_fbv, name='fbv-encomienda-detail'),
    path('apiview/encomiendas/', views.EncomiendaListAPIView.as_view(), name='apiview-encomienda-list'),
    path('apiview/encomiendas/<int:pk>/', views.EncomiendaDetailAPIView.as_view(), name='apiview-encomienda-detail'),
    path('mixins/encomiendas/', views.EncomiendaMixinListCreateView.as_view(), name='mixin-encomienda-list'),
    path('mixins/encomiendas/<int:pk>/', views.EncomiendaMixinDetailView.as_view(), name='mixin-encomienda-detail'),
    path('generic/encomiendas/', views.EncomiendaListCreateView.as_view(), name='generic-encomienda-list'),
    path('generic/encomiendas/<int:pk>/', views.EncomiendaDetailView.as_view(), name='generic-encomienda-detail'),
    path('generic/clientes/', views.ClienteListView.as_view(), name='generic-cliente-list'),
    path('generic/rutas/', views.RutaListView.as_view(), name='generic-ruta-list'),
    path('', include(router.urls)),
]
