from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, UpdateView, DeleteView
from apps.empleados_app.models import Empleado
from .forms import DetalleAsistenciaForm, MarcarAsistenciaForm
from .models import RegistroAsistencia
from .services import AsistenciaError, cerrar_vencidas, registrar_ingreso, registrar_salida


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


def _formato(momento):
    return timezone.localtime(momento).strftime("%d/%m/%Y %H:%M")


class AsistenciaListView(AdminMixin, ListView):
    model = RegistroAsistencia
    template_name = "asistencias/panel.html"
    paginate_by = 20
    titulo = "Asistencias"
    descripcion = "Registrá el ingreso y la salida del equipo."
    columnas = ("Empleado", "Ingreso", "Salida", "Comisión diaria", "Detalle")
    lista_url = reverse_lazy("asistencias:lista")

    def get(self, request, *args, **kwargs):
        cerrar_vencidas()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("empleado")
        termino = self.request.GET.get("q", "").strip()[:100]
        if termino:
            qs = qs.filter(
                Q(empleado__nombre__icontains=termino) | Q(empleado__apellido__icontains=termino)
            )
        return qs

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
                ),
                "editar_url": reverse_lazy("asistencias:editar", args=[o.pk]),
                "eliminar_url": reverse_lazy("asistencias:eliminar", args=[o.pk]),
            }
            for o in ctx["object_list"]
        ]
        return ctx

    def _empleados_con_estado(self):
        de_hoy = {
            a.empleado_id: a
            for a in RegistroAsistencia.objects.filter(
                fecha_hora_ingreso__date=timezone.localdate()
            )
        }
        resultado = []
        for empleado in Empleado.objects.filter(estado="Activo"):
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
        if form.cleaned_data["accion"] == "ingreso":
            asistencia = registrar_ingreso(empleado)
            hora = timezone.localtime(asistencia.fecha_hora_ingreso).strftime("%H:%M")
            messages.success(request, f"Ingreso de {empleado} registrado a las {hora}.")
        else:
            asistencia = registrar_salida(empleado)
            messages.success(
                request,
                f"Salida de {empleado} registrada. Comisión del día: $ {asistencia.comision_diaria}.",
            )
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


class AsistenciaDeleteView(AdminMixin, DeleteView):
    model = RegistroAsistencia
    template_name = "componentes/crud_confirmar.html"
    success_url = reverse_lazy("asistencias:lista")
    extra_context = {"titulo": "Eliminar asistencia", "lista_url": success_url}

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: tiene servicios realizados.")
            return redirect(self.success_url)
        messages.success(self.request, "Registro eliminado.")
        return response
