from decimal import Decimal
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from apps.asistencias_app.models import RegistroAsistencia
from apps.asistencias_app.services import cerrar_vencidas
from apps.empleados_app.mixins import EmpleadoSoloLecturaMixin
from apps.empleados_app.models import Empleado
from apps.listados import ListadoMixin

from .forms import ServicioForm, RegistrarServicioForm, EditarRealizadoForm
from .services import ServicioError, cambiar_estado_realizado
from .models import Servicio, ServicioRealizado


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self): return self.request.user.is_superuser


class TablaAdminMixin(AdminMixin, ListadoMixin, ListView):
    template_name = "componentes/crud_lista.html"; paginate_by = 20; columnas = ()
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(titulo=self.titulo, descripcion=self.descripcion, columnas=self.columnas, crear_url=self.crear_url, lista_url=self.lista_url)
        ctx["filas"] = [{"valores": self.valores(obj), "editar_url": self.editar_url(obj), "eliminar_url": self.eliminar_url(obj), "baja_texto": self.baja_texto(obj), "inhabilitada": not obj.activo} for obj in ctx["object_list"]]
        return ctx
    def baja_texto(self, obj):
        return "Inhabilitar"


class ServicioListView(TablaAdminMixin):
    model = Servicio; titulo = "Servicios"; descripcion = "Servicios disponibles en la estética."
    columnas = ("Servicio", "Descripción", "Precio"); busqueda = ("nombre_servicio", "descripcion")
    crear_url = reverse_lazy("operaciones:servicio_crear"); lista_url = reverse_lazy("operaciones:servicios")
    ordenes = (
        ("nombre", "Nombre (A-Z)", ("nombre_servicio",)),
        ("-nombre", "Nombre (Z-A)", ("-nombre_servicio",)),
        ("precio", "Precio (menor a mayor)", ("precio",)),
        ("-precio", "Precio (mayor a menor)", ("-precio",)),
    )
    
    def valores(self, o): return (o.nombre_servicio, o.descripcion, f"$ {o.precio}","habilitado" if o.activo else "inhabilitado")
    def editar_url(self, o): return reverse_lazy("operaciones:servicio_editar", args=[o.pk])
    def eliminar_url(self, o): return reverse_lazy("operaciones:servicio_eliminar", args=[o.pk])
    def baja_texto(self, o): return "Inhabilitar" if o.activo else "Habilitar"


class RealizadoListView(TablaAdminMixin):
    model = ServicioRealizado
    titulo = "Servicios realizados"
    descripcion = "Consultá los servicios realizados."
    columnas = ("Fecha y hora", "Servicio", "Empleado", "Monto", "Estado")
    busqueda = ("servicio__nombre_servicio", "empleado__nombre", "empleado__apellido")
    crear_url = reverse_lazy("operaciones:realizado_crear")
    lista_url = reverse_lazy("operaciones:realizados")
    ordenes = (
        ("-fecha", "Fecha (más reciente)", ("-fecha_hora",)),
        ("fecha", "Fecha (más antigua)", ("fecha_hora",)),
        ("nombre", "Nombre (A-Z)", ("empleado__apellido", "empleado__nombre")),
        ("-nombre", "Nombre (Z-A)", ("-empleado__apellido", "-empleado__nombre")),
    )
    campo_fecha = "fecha_hora"
    filtros = (
        {
            "param": "empleado", "etiqueta": "Empleado", "campo": "empleado",
            "opciones": lambda: [(str(e.pk), str(e), e.pk) for e in Empleado.objects.all()],
        },
        {
            "param": "servicio", "etiqueta": "Servicio", "campo": "servicio",
            "opciones": lambda: [(str(s.pk), s.nombre_servicio, s.pk) for s in Servicio.objects.all()],
        },
        {
            "param": "estado", "etiqueta": "Estado", "campo": "activo",
            "opciones": [("activo", "Activo", True), ("inhabilitado", "Inhabilitado", False)],
        },
    )


    def get_queryset(self):
        return super().get_queryset().select_related("servicio", "empleado")

    def valores(self, o):
        return (
            timezone.localtime(o.fecha_hora).strftime("%d/%m/%Y %H:%M"),
            o.servicio.nombre_servicio,
            str(o.empleado),
            f"$ {o.monto_servicio}",
            "Activo" if o.activo else "Inhabilitado",
        )

    def editar_url(self, o): return reverse_lazy("operaciones:realizado_editar", args=[o.pk])
    def eliminar_url(self, o): return reverse_lazy("operaciones:realizado_estado", args=[o.pk])
    def baja_texto(self, o): return "Inhabilitar" if o.activo else "Habilitar"



class MisServiciosListView(EmpleadoSoloLecturaMixin, ListadoMixin, ListView):
    model = ServicioRealizado
    template_name = "componentes/crud_lista.html"
    paginate_by = 20
    columnas = ("Fecha y hora", "Servicio", "Monto", "Tu comisión (40%)")
    busqueda = ("servicio__nombre_servicio",)
    ordenes = (
        ("-fecha", "Fecha (más reciente)", ("-fecha_hora",)),
        ("fecha", "Fecha (más antigua)", ("fecha_hora",)),
        ("-monto", "Monto (mayor a menor)", ("-monto_servicio",)),
        ("monto", "Monto (menor a mayor)", ("monto_servicio",)),
    )
    campo_fecha = "fecha_hora"
    filtros = ()

    def _filtros_resueltos(self):
        propios = ServicioRealizado.objects.filter(activo=True, empleado=self.request.user.empleado)
        servicios = Servicio.objects.filter(pk__in=propios.values("servicio"))
        self.filtros = (
            {
                "param": "servicio", "etiqueta": "Servicio", "campo": "servicio",
                "opciones": lambda: [(str(s.pk), s.nombre_servicio, s.pk) for s in servicios],
            },
        )
        return super()._filtros_resueltos()

    def get_queryset(self):
        propios = super().get_queryset().filter(activo=True, empleado=self.request.user.empleado)
        return propios.select_related("servicio")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            titulo="Mis servicios realizados",
            descripcion="Consultá los servicios que realizaste y tu comisión.",
            columnas=self.columnas,
            solo_lectura=True,
        )
        ctx["filas"] = [{"valores": self._valores(o)} for o in ctx["object_list"]]
        return ctx

    def _valores(self, o):
        comision = (o.monto_servicio * RegistroAsistencia.PORCENTAJE_COMISION).quantize(Decimal("0.01"))
        return (
            timezone.localtime(o.fecha_hora).strftime("%d/%m/%Y %H:%M"),
            o.servicio.nombre_servicio,
            f"$ {o.monto_servicio}",
            f"$ {comision}",
        )


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
    form_class = EditarRealizadoForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("operaciones:realizados")
    titulo = "Editar servicio realizado"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.asistencia_en_curso:
            messages.error(request, EditarRealizadoForm.MENSAJE)
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


class RealizadoEstadoView(AdminMixin, DetailView):
    model = ServicioRealizado
    template_name = "componentes/crud_estado.html"

    def post(self, request, *args, **kwargs):
        realizado = self.get_object()
        try:
            cambiar_estado_realizado(realizado, not realizado.activo)
        except ServicioError as error:
            messages.error(request, str(error))
        else:
            realizado.refresh_from_db()
            messages.success(
                request,
                f"Servicio realizado {'habilitado' if realizado.activo else 'inhabilitado'}.",
            )
        return redirect("operaciones:realizados")



class ServicioEstadoView(AdminMixin, DetailView):
    model = Servicio
    template_name="componentes/crud_estado.html"

    def post(self, request, *args, **kwargs):
        servicio = self.get_object()
        servicio.activo = not servicio.activo
        servicio.save(update_fields=["activo"])
        messages.success(request, f"Servicio {'habilitado' if servicio.activo else 'inhabilitado'}.")
        return redirect("operaciones:servicios")


for _view in (ServicioCreateView, ServicioUpdateView, RealizadoCreateView, RealizadoUpdateView):
    _view.extra_context = {"titulo": _view.titulo, "lista_url": _view.success_url}

RealizadoEstadoView.extra_context = {
    "lista_url": reverse_lazy("operaciones:realizados"),
    "entidad": "servicio realizado",
    "consecuencia_baja": "Dejará de contar en la comisión diaria y en los totales del mes, pero se conserva el registro.",
    "consecuencia_alta": "Volverá a contar en la comisión diaria y en los totales del mes.",
}


ServicioEstadoView.extra_context = {
    "lista_url": reverse_lazy("operaciones:servicios"),
    "entidad": "servicio",
    "consecuencia_baja": "Ya no se podrá registrar en nuevos servicios realizados, pero se conserva todo su historial.",
    "consecuencia_alta": "Volverá a estar disponible para registrar servicios.",
}