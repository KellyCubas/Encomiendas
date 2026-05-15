from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from config.choices import EstadoEnvio
from .forms import EncomiendaForm
from .models import Empleado, Encomienda


def _empleado_actual(request):
    if not request.user.email:
        return Empleado.objects.activos().first()
    return Empleado.objects.filter(email=request.user.email).first() or Empleado.objects.activos().first()


@login_required
def dashboard(request):
    hoy = timezone.now().date()
    context = {
        'total_activas': Encomienda.objects.activas().count(),
        'en_transito': Encomienda.objects.en_transito().count(),
        'con_retraso': Encomienda.objects.con_retraso().count(),
        'entregadas_hoy': Encomienda.objects.filter(
            estado=EstadoEnvio.ENTREGADO,
            fecha_entrega_real=hoy
        ).count(),
        'ultimas': Encomienda.objects.con_relaciones()[:5],
    }
    context['stats'] = [
        ('Activas', context['total_activas'], 'primary', 'box'),
        ('En transito', context['en_transito'], 'warning', 'truck'),
        ('Con retraso', context['con_retraso'], 'danger', 'clock'),
        ('Entregadas hoy', context['entregadas_hoy'], 'success', 'check'),
    ]
    return render(request, 'envios/dashboard.html', context)


@login_required
def encomienda_lista(request):
    estado = request.GET.get('estado', '')
    q = request.GET.get('q', '')

    qs = Encomienda.objects.con_relaciones()
    if estado:
        qs = qs.filter(estado=estado)
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q)
            | Q(remitente__apellidos__icontains=q)
            | Q(destinatario__apellidos__icontains=q)
            | Q(ruta__destino__icontains=q)
        )

    paginator = Paginator(qs, 15)
    encomiendas = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'envios/lista.html', {
        'encomiendas': encomiendas,
        'estados': EstadoEnvio.choices,
        'estado_activo': estado,
        'q': q,
    })


@login_required
def encomienda_detalle(request, pk):
    encomienda = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    return render(request, 'envios/detalle.html', {
        'encomienda': encomienda,
        'historial': encomienda.historial.select_related('empleado').all(),
        'estados': EstadoEnvio.choices,
    })


@login_required
def encomienda_crear(request):
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            empleado = _empleado_actual(request)
            if empleado is None:
                messages.error(request, 'No existe un empleado activo para registrar la encomienda.')
                return render(request, 'envios/form.html', {'form': form, 'titulo': 'Nueva Encomienda'})

            enc = form.save(commit=False)
            enc.empleado_registro = empleado
            enc.save()
            messages.success(request, f'Encomienda {enc.codigo} registrada correctamente.')
            return redirect('encomienda_detalle', pk=enc.pk)
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = EncomiendaForm()

    return render(request, 'envios/form.html', {
        'form': form,
        'titulo': 'Nueva Encomienda',
    })


@login_required
@require_POST
def encomienda_cambiar_estado(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    nuevo_estado = request.POST.get('estado')
    observacion = request.POST.get('observacion', '')
    empleado = _empleado_actual(request)

    if empleado is None:
        raise PermissionDenied('No existe un empleado activo asociado para cambiar estados.')

    try:
        encomienda.cambiar_estado(nuevo_estado, empleado, observacion)
        messages.success(request, f'Estado actualizado a: {encomienda.get_estado_display()}')
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect('encomienda_detalle', pk=pk)


@login_required
def encomienda_estado_json(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    return JsonResponse({
        'codigo': encomienda.codigo,
        'estado': encomienda.estado,
        'display': encomienda.get_estado_display(),
        'retraso': encomienda.tiene_retraso,
        'dias': encomienda.dias_en_transito,
    })
