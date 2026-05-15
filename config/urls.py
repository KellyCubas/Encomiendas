from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

admin.site.site_header = 'Sistema de Gestion de Encomiendas'
admin.site.site_title = 'Encomiendas Admin'
admin.site.index_title = 'Panel de Administracion'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('envios.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
