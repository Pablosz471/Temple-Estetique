from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, TemplateView
from apps.empleados_app.models import Empleado
from apps.listados import ListadoMixin
from apps.mixins import AdminMixin, EmpleadoSoloLecturaMixin
from apps.servicios_app.models import Servicio
from .models import RegistroMensual


class LiquidacionesView(AdminMixin, TemplateView):
    template_name = "liquidaciones/lista.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            empleados=Empleado.objects.all(),
            empleado=None,
            registros=[],
            meses=[],
            mes_elegido="",
        )
        empleado_id = self.request.GET.get("empleado", "")
        if empleado_id.isdigit():
            empleado = get_object_or_404(Empleado, pk=empleado_id)
            ctx.update(_meses_de(empleado, self.request.GET.get("mes", "")))
        return ctx


def _meses_de(empleado, mes_elegido):
    hoy = timezone.localdate()
    # El mes en curso aparece siempre y con los números al día.
    RegistroMensual.actualizar(empleado.pk, hoy.year, hoy.month)
    todos = list(empleado.registros_mensuales.all())
    meses = [(r.clave, r.periodo) for r in todos]
    if mes_elegido not in dict(meses):
        mes_elegido = ""
    registros = [r for r in todos if not mes_elegido or r.clave == mes_elegido]
    RegistroMensual.cargar_resumenes(empleado, registros)
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


class ServiciosDelMesView(AdminMixin, _ListadoServiciosDelMes):
    pass


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
