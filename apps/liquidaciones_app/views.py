from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView, TemplateView
from apps.empleados_app.mixins import EmpleadoSoloLecturaMixin
from apps.empleados_app.models import Empleado
from apps.listados import ListadoMixin
from apps.servicios_app.models import Servicio
from .models import RegistroMensual


def _exigir_admin(request):
    if not request.user.is_superuser:
        raise PermissionDenied


@login_required
def lista(request):
    _exigir_admin(request)
    contexto = {
        "empleados": Empleado.objects.all(),
        "empleado": None,
        "registros": [],
        "meses": [],
        "mes_elegido": "",
    }
    empleado_id = request.GET.get("empleado", "")
    if empleado_id.isdigit():
        empleado = get_object_or_404(Empleado, pk=empleado_id)
        contexto.update(_meses_de(empleado, request.GET.get("mes", "")))
    return render(request, "liquidaciones/lista.html", contexto)


def _meses_de(empleado, mes_elegido):
    hoy = timezone.localdate()
    # El mes en curso aparece siempre y con los números al día.
    RegistroMensual.actualizar(empleado.pk, hoy.year, hoy.month)
    todos = list(empleado.registros_mensuales.all())
    meses = [(r.clave, r.periodo) for r in todos]
    if mes_elegido not in dict(meses):
        mes_elegido = ""
    registros = [r for r in todos if not mes_elegido or r.clave == mes_elegido]
    for registro in registros:
        registro.ultimos = list(registro.servicios()[:5])
        registro.cantidad = registro.servicios().count()
    return {"empleado": empleado, "registros": registros, "meses": meses, "mes_elegido": mes_elegido}


class _ServiciosDelMes(ListView):
    template_name = "liquidaciones/servicios.html"
    paginate_by = 20

    def buscar_registro(self):
        return get_object_or_404(RegistroMensual, pk=self.kwargs["pk"])

    def get_queryset(self):
        registro = self.buscar_registro()
        self.registro = RegistroMensual.actualizar(registro.empleado_id, registro.anio, registro.mes)
        return self.registro.servicios()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["registro"] = self.registro
        return ctx


class _ListadoServiciosDelMes(ListadoMixin, _ServiciosDelMes):
    busqueda = ("servicio__nombre_servicio",)
    ordenes = (
        ("-fecha", "Fecha (más reciente)", ("-fecha_hora",)),
        ("fecha", "Fecha (más antigua)", ("fecha_hora",)),
        ("-monto", "Monto (mayor a menor)", ("-monto_servicio",)),
        ("monto", "Monto (menor a mayor)", ("monto_servicio",)),
    )
    campo_fecha = "fecha_hora"

    @property
    def filtros(self):
        return (
            {
                "param": "servicio", "etiqueta": "Servicio", "campo": "servicio",
                "opciones": self._opciones_de_servicio,
            },
        )

    def _opciones_de_servicio(self):
        realizados = self.registro.servicios().values("servicio")
        return [(str(s.pk), s.nombre_servicio, s.pk) for s in Servicio.objects.filter(pk__in=realizados)]


class ServiciosDelMesView(LoginRequiredMixin, UserPassesTestMixin, _ListadoServiciosDelMes):
    def test_func(self):
        return self.request.user.is_superuser


class MisLiquidacionesView(EmpleadoSoloLecturaMixin, TemplateView):
    template_name = "liquidaciones/lista.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_meses_de(self.request.user.empleado, self.request.GET.get("mes", "")))
        ctx["solo_lectura"] = True
        return ctx


class MisServiciosDelMesView(EmpleadoSoloLecturaMixin, _ListadoServiciosDelMes):
    def buscar_registro(self):
        return get_object_or_404(
            RegistroMensual, pk=self.kwargs["pk"], empleado=self.request.user.empleado
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["solo_lectura"] = True
        return ctx
