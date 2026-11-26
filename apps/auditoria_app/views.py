from django.views.generic import ListView
from apps.listados import ListadoMixin
from apps.mixins import AdminMixin
from .models import RegistroCambio


def _distintos(campo):
    valores = RegistroCambio.objects.order_by().values_list(campo, flat=True).distinct()
    return [(v, v, v) for v in sorted(valores) if v]


class HistorialListView(AdminMixin, ListadoMixin, ListView):
    model = RegistroCambio
    template_name = "auditoria/lista.html"
    paginate_by = 30
    busqueda = ("usuario_nombre", "modelo", "objeto", "detalle")
    ordenes = (
        ("-fecha", "Fecha (más reciente)", ("-fecha_hora",)),
        ("fecha", "Fecha (más antigua)", ("fecha_hora",)),
        ("nombre", "Nombre (A-Z)", ("usuario_nombre",)),
        ("-nombre", "Nombre (Z-A)", ("-usuario_nombre",)),
    )
    campo_fecha = "fecha_hora"
    filtros = (
        {
            "param": "empleado", "etiqueta": "Empleado",
            "campo": "usuario_nombre", "opciones": lambda: _distintos("usuario_nombre"),
        },
        {
            "param": "accion", "etiqueta": "Acción", "campo": "accion",
            "opciones": [
                (v, e, v)
                for v, e in RegistroCambio.Accion.choices
                if v != RegistroCambio.Accion.ELIMINACION
            ],
        },
        {
            "param": "seccion", "etiqueta": "Sección",
            "campo": "modelo", "opciones": lambda: _distintos("modelo"),
        },
    )
