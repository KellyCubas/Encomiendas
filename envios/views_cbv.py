from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from config.choices import EstadoEnvio
from .forms import EncomiendaForm
from .models import Empleado, Encomienda


class EncomiendaListView(LoginRequiredMixin, ListView):
    model = Encomienda
    template_name = 'envios/lista.html'
    context_object_name = 'encomiendas'
    paginate_by = 15

    def get_queryset(self):
        qs = Encomienda.objects.con_relaciones()
        estado = self.request.GET.get('estado', '')
        q = self.request.GET.get('q', '')
        if estado:
            qs = qs.filter(estado=estado)
        if q:
            qs = qs.filter(codigo__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = EstadoEnvio.choices
        context['estado_activo'] = self.request.GET.get('estado', '')
        context['q'] = self.request.GET.get('q', '')
        return context


class EncomiendaDetailView(LoginRequiredMixin, DetailView):
    model = Encomienda
    template_name = 'envios/detalle.html'
    context_object_name = 'encomienda'

    def get_queryset(self):
        return Encomienda.objects.con_relaciones()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historial'] = self.object.historial.select_related('empleado').all()
        context['estados'] = EstadoEnvio.choices
        return context


class EncomiendaCreateView(LoginRequiredMixin, CreateView):
    model = Encomienda
    form_class = EncomiendaForm
    template_name = 'envios/form.html'

    def form_valid(self, form):
        empleado = Empleado.objects.filter(email=self.request.user.email).first() or Empleado.objects.activos().first()
        if empleado is None:
            form.add_error(None, 'No existe un empleado activo para registrar la encomienda.')
            return self.form_invalid(form)
        form.instance.empleado_registro = empleado
        messages.success(self.request, f'Encomienda {form.instance.codigo} registrada correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('encomienda_detalle', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Encomienda'
        return context


class EncomiendaUpdateView(LoginRequiredMixin, UpdateView):
    model = Encomienda
    form_class = EncomiendaForm
    template_name = 'envios/form.html'

    def get_success_url(self):
        return reverse_lazy('encomienda_detalle', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Encomienda'
        return context
