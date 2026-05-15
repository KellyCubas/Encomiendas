from django.urls import path
from . import views
from . import views_cbv


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('encomiendas/', views.encomienda_lista, name='encomienda_lista'),
    path('encomiendas/nueva/', views.encomienda_crear, name='encomienda_crear'),
    path('encomiendas/<int:pk>/', views.encomienda_detalle, name='encomienda_detalle'),
    path('encomiendas/<int:pk>/estado/', views.encomienda_cambiar_estado, name='encomienda_cambiar_estado'),
    path('encomiendas/<int:pk>/estado/json/', views.encomienda_estado_json, name='encomienda_estado_json'),
    path('cbv/encomiendas/', views_cbv.EncomiendaListView.as_view(), name='encomienda_lista_cbv'),
    path('cbv/encomiendas/nueva/', views_cbv.EncomiendaCreateView.as_view(), name='encomienda_crear_cbv'),
    path('cbv/encomiendas/<int:pk>/', views_cbv.EncomiendaDetailView.as_view(), name='encomienda_detalle_cbv'),
    path('cbv/encomiendas/<int:pk>/editar/', views_cbv.EncomiendaUpdateView.as_view(), name='encomienda_editar_cbv'),
]
