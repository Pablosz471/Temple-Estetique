from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .forms import ServicioForm, RegistrarServicioForm, ObservacionServicioForm
from apps.asistencias_app.services import cerrar_vencidas
from .models import Servicio, ServicioRealizado


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self): return self.request.user.is_superuser


class TablaAdminMixin(AdminMixin, ListView):
    template_name = "componentes/crud_lista.html"; paginate_by = 20; columnas = (); busqueda = ()
    def get_queryset(self):
        qs = super().get_queryset(); termino = self.request.GET.get("q", "").strip()[:100]
        if termino and self.busqueda:
            filtro = Q()
            for campo in self.busqueda: filtro |= Q(**{f"{campo}__icontains": termino})
            qs = qs.filter(filtro)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(titulo=self.titulo, descripcion=self.descripcion, columnas=self.columnas, crear_url=self.crear_url, lista_url=self.lista_url)
        ctx["filas"] = [{"valores": self.valores(obj), "editar_url": self.editar_url(obj), "eliminar_url": self.eliminar_url(obj), "baja_texto":self.baja_texto(obj)} for obj in ctx["object_list"]]
        return ctx
    def baja_texto(self, obj):
        return "Inhabilitar"


class ServicioListView(TablaAdminMixin):
    model = Servicio; titulo = "Servicios"; descripcion = "Servicios disponibles en la estética."
    columnas = ("Servicio", "Descripción", "Precio"); busqueda = ("nombre_servicio", "descripcion")
    crear_url = reverse_lazy("operaciones:servicio_crear"); lista_url = reverse_lazy("operaciones:servicios")
    def valores(self, o): return (o.nombre_servicio, o.descripcion, f"$ {o.precio}","habilitado" if o.activo else "inhabilitado")
    def editar_url(self, o): return reverse_lazy("operaciones:servicio_editar", args=[o.pk])
    def eliminar_url(self, o): return reverse_lazy("operaciones:servicio_eliminar", args=[o.pk])
    def baja_texto(self, o): return "Inhabilitar" if o.activo else "Habilitar"


class RealizadoListView(TablaAdminMixin):
    model = ServicioRealizado
    titulo = "Servicios realizados"
    descripcion = "Consultá los servicios realizados."
    columnas = ("Fecha y hora", "Servicio", "Empleado", "Monto")
    busqueda = ("servicio__nombre_servicio", "empleado__nombre", "empleado__apellido")
    crear_url = reverse_lazy("operaciones:realizado_crear")
    lista_url = reverse_lazy("operaciones:realizados")

    def get_queryset(self):
        return super().get_queryset().select_related("servicio", "empleado")

    def valores(self, o):
        return (
            timezone.localtime(o.fecha_hora).strftime("%d/%m/%Y %H:%M"),
            o.servicio.nombre_servicio,
            str(o.empleado),
            f"$ {o.monto_servicio}",
        )

    def editar_url(self, o): return reverse_lazy("operaciones:realizado_editar", args=[o.pk])
    def eliminar_url(self, o): return reverse_lazy("operaciones:realizado_eliminar", args=[o.pk])


class GuardarMixin:
    def form_valid(self, form): messages.success(self.request, "Cambios guardados correctamente."); return super().form_valid(form)


class ServicioCreateView(AdminMixin, GuardarMixin, CreateView):
    model = Servicio; form_class = ServicioForm; template_name = "componentes/crud_form.html"; success_url = reverse_lazy("operaciones:servicios"); titulo = "Agregar servicio"
class ServicioUpdateView(AdminMixin, GuardarMixin, UpdateView):
    model = Servicio; form_class = ServicioForm; template_name = "componentes/crud_form.html"; success_url = reverse_lazy("operaciones:servicios"); titulo = "Editar servicio"

class RealizadoCreateView(AdminMixin, GuardarMixin, CreateView):
    model = ServicioRealizado
    form_class = RegistrarServicioForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("operaciones:realizados")
    titulo = "Registrar servicio realizado"

    def get(self, request, *args, **kwargs):
        cerrar_vencidas()
        return super().get(request, *args, **kwargs)

class RealizadoUpdateView(AdminMixin, GuardarMixin, UpdateView):
    model = ServicioRealizado
    form_class = ObservacionServicioForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("operaciones:realizados")
    titulo = "Editar observación"


class BajaMixin(AdminMixin, DeleteView):
    template_name = "componentes/crud_confirmar.html"
    def form_valid(self, form):
        try: response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: hay servicios realizados relacionados.")
            return redirect(self.success_url)
        messages.success(self.request, "Registro eliminado."); return response
class ServicioEstadoView(AdminMixin, DetailView):
    model = Servicio
    template_name="componentes/crud_estado.html"

    def post(self, request, *args, **kwargs):
        servicio = self.get_object()
        servicio.activo = not servicio.activo
        servicio.save(update_fields=["activo"])
        messages.success(request, f"Servicio {'habilitado' if servicio.activo else 'inhabilitado'}.")
        return redirect("operaciones:servicios")

class RealizadoDeleteView(BajaMixin): model = ServicioRealizado; success_url = reverse_lazy("operaciones:realizados"); titulo = "Eliminar registro"

for _view in (ServicioCreateView, ServicioUpdateView, RealizadoCreateView, RealizadoUpdateView):
    _view.extra_context = {"titulo": _view.titulo, "lista_url": _view.success_url}

RealizadoDeleteView.extra_context = {"titulo": RealizadoDeleteView.titulo, "lista_url": RealizadoDeleteView.success_url}


ServicioEstadoView.extra_context = {
    "lista_url": reverse_lazy("operaciones:servicios"),
    "entidad": "servicio",
    "consecuencia_baja": "Ya no se podrá registrar en nuevos servicios realizados, pero se conserva todo su historial.",
    "consecuencia_alta": "Volverá a estar disponible para registrar servicios.",
}