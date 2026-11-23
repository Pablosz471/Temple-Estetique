from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, UpdateView, DetailView

from apps.empleados_app.models import Empleado
from apps.listados import ListadoMixin

from .forms import DetalleAsistenciaForm, MarcarAsistenciaForm
from .models import RegistroAsistencia
from .services import (AsistenciaError, cambiar_estado_asistencia, cerrar_vencidas, reabrir_asistencia, registrar_ingreso, registrar_salida,)


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


def _formato(momento):
    return timezone.localtime(momento).strftime("%d/%m/%Y %H:%M")


class AsistenciaListView(AdminMixin, ListadoMixin, ListView):
    model = RegistroAsistencia
    template_name = "asistencias/panel.html"
    paginate_by = 20
    titulo = "Asistencias"
    descripcion = "Registrá el ingreso y la salida del equipo."
    columnas = ("Empleado", "Ingreso", "Salida", "Comisión diaria", "Detalle", "Estado")
    lista_url = reverse_lazy("asistencias:lista")
    busqueda = ("empleado__nombre", "empleado__apellido")
    ordenes = (
        ("-fecha", "Fecha (más reciente)", ("-fecha_hora_ingreso",)),
        ("fecha", "Fecha (más antigua)", ("fecha_hora_ingreso",)),
        ("nombre", "Nombre (A-Z)", ("empleado__apellido", "empleado__nombre")),
        ("-nombre", "Nombre (Z-A)", ("-empleado__apellido", "-empleado__nombre")),
        ("-comision", "Comisión (mayor a menor)", ("-comision_diaria",)),
        ("comision", "Comisión (menor a mayor)", ("comision_diaria",)),
    )
    campo_fecha = "fecha_hora_ingreso"
    filtros = (
        {
            "param": "empleado", "etiqueta": "Empleado", "campo": "empleado",
            "opciones": lambda: [(str(e.pk), str(e), e.pk) for e in Empleado.objects.all()],
        },
        {
            "param": "situacion", "etiqueta": "Situación", "campo": "fecha_hora_salida__isnull",
            "opciones": [("encurso", "En curso", True), ("cerrada", "Cerrada", False)],
        },
        {
            "param": "registro", "etiqueta": "Registro", "campo": "activo",
            "opciones": [("activa", "Activa", True), ("inhabilitada", "Inhabilitada", False)],
        },
    )


    def get(self, request, *args, **kwargs):
        cerrar_vencidas()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().select_related("empleado")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            titulo=self.titulo,
            descripcion=self.descripcion,
            columnas=self.columnas,
            crear_url="",
            lista_url=self.lista_url,
            empleados=self._empleados_con_estado(),
        )
        ctx["filas"] = [
            {
                "valores": (
                    str(o.empleado),
                    _formato(o.fecha_hora_ingreso),
                    _formato(o.fecha_hora_salida) if o.fecha_hora_salida else "En curso",
                    "Se calcula a la salida" if o.abierta else f"$ {o.comision_diaria}",
                    o.detalle or "—",
                    "Activa" if o.activo else "Inhabilitada",
                ),
                "editar_url": reverse_lazy("asistencias:editar", args=[o.pk]),
                "eliminar_url": reverse_lazy("asistencias:estado", args=[o.pk]),
                "baja_texto": "Inhabilitar" if o.activo else "Habilitar",
            }
            for o in ctx["object_list"]
        ]
        return ctx

    def _empleados_con_estado(self):
        de_hoy = {
            a.empleado_id: a
            for a in RegistroAsistencia.objects.filter(
                activo=True, fecha_hora_ingreso__date=timezone.localdate()
            )
        }
        resultado = []
        for empleado in Empleado.objects.filter(activo=True):
            asistencia = de_hoy.get(empleado.pk)
            if asistencia is None:
                estado = "sin"
            elif asistencia.abierta:
                estado = "abierta"
            else:
                estado = "cerrada"
            resultado.append({"empleado": empleado, "estado": estado})
        return resultado


@login_required
@require_POST
def marcar(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    form = MarcarAsistenciaForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Elegí un empleado activo y una acción válida.")
        return redirect("asistencias:lista")
    empleado = form.cleaned_data["empleado"]
    try:
        accion = form.cleaned_data["accion"]
        if accion == "ingreso":
            asistencia = registrar_ingreso(empleado)
            hora = timezone.localtime(asistencia.fecha_hora_ingreso).strftime("%H:%M")
            messages.success(request, f"Ingreso de {empleado} registrado a las {hora}.")
        elif accion == "salida":
            asistencia = registrar_salida(empleado)
            messages.success(
                request,
                f"Salida de {empleado} registrada. Comisión del día: $ {asistencia.comision_diaria}.",
            )
        else:
            reabrir_asistencia(empleado)
            messages.success(request, f"Asistencia de {empleado} reabierta.")
    except AsistenciaError as error:
        messages.error(request, str(error))
    return redirect("asistencias:lista")


class AsistenciaUpdateView(AdminMixin, UpdateView):
    model = RegistroAsistencia
    form_class = DetalleAsistenciaForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("asistencias:lista")
    extra_context = {"titulo": "Editar detalle de asistencia", "lista_url": success_url}

    def form_valid(self, form):
        messages.success(self.request, "Detalle guardado correctamente.")
        return super().form_valid(form)


class AsistenciaEstadoView(AdminMixin, DetailView):
    model = RegistroAsistencia
    template_name = "componentes/crud_estado.html"
    extra_context = {
        "lista_url": reverse_lazy("asistencias:lista"),
        "entidad": "asistencia",
        "consecuencia_baja": "Dejará de contar como la asistencia del día y el empleado podrá registrar una nueva. Se conserva el registro.",
        "consecuencia_alta": "Volverá a contar como la asistencia de ese día.",
    }

    def post(self, request, *args, **kwargs):
        asistencia = self.get_object()
        try:
            cambiar_estado_asistencia(asistencia, not asistencia.activo)
        except AsistenciaError as error:
            messages.error(request, str(error))
        else:
            asistencia.refresh_from_db()
            messages.success(
                request, f"Asistencia {'habilitada' if asistencia.activo else 'inhabilitada'}."
            )
        return redirect("asistencias:lista")
