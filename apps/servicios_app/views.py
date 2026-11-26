from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView

from apps.asistencias_app.services import cerrar_vencidas
from apps.empleados_app.models import Empleado
from apps.formatos import fecha_hora
from apps.mixins import AdminMixin, GuardarMixin, TablaAdminMixin

from .forms import ServicioForm, RegistrarServicioForm, EditarRealizadoForm
from .services import ServicioError, cambiar_estado_realizado
from .models import Servicio, ServicioRealizado


class ServicioListView(TablaAdminMixin):
    model = Servicio; titulo = "Servicios"; descripcion = "Servicios disponibles en la estética."
    columnas = ("Servicio", "Descripción", "Precio", "Estado"); busqueda = ("nombre_servicio", "descripcion")
    crear_url = reverse_lazy("operaciones:servicio_crear"); lista_url = reverse_lazy("operaciones:servicios")
    ordenes = (
        ("nombre", "Nombre (A-Z)", ("nombre_servicio",)),
        ("-nombre", "Nombre (Z-A)", ("-nombre_servicio",)),
        ("precio", "Precio (menor a mayor)", ("precio",)),
        ("-precio", "Precio (mayor a menor)", ("-precio",)),
    )
    
    def valores(self, o): return (o.nombre_servicio, o.descripcion, f"$ {o.precio}","Habilitado" if o.activo else "Inhabilitado")
    def editar_url(self, o): return reverse_lazy("operaciones:servicio_editar", args=[o.pk])
    def eliminar_url(self, o): return reverse_lazy("operaciones:servicio_eliminar", args=[o.pk])


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
            fecha_hora(o.fecha_hora),
            o.servicio.nombre_servicio,
            str(o.empleado),
            f"$ {o.monto_servicio}",
            "Activo" if o.activo else "Inhabilitado",
        )

    def editar_url(self, o): return reverse_lazy("operaciones:realizado_editar", args=[o.pk])
    def eliminar_url(self, o): return reverse_lazy("operaciones:realizado_estado", args=[o.pk])



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