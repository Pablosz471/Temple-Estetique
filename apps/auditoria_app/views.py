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
    paso = 10  # registros iniciales y cuántos agrega cada "Ver más"
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

    def get_paginate_by(self, queryset):
        try:
            pedido = int(self.request.GET.get("mostrar", ""))
        except ValueError:
            return self.paso
        return max(pedido, self.paso)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pagina = ctx["page_obj"]
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        if pagina.has_next():
            parametros["mostrar"] = pagina.paginator.per_page + self.paso
            ctx["ver_mas_querystring"] = parametros.urlencode()
        if len(pagina) > self.paso:
            parametros.pop("mostrar", None)
            ctx["hay_ver_menos"] = True
            ctx["ver_menos_querystring"] = parametros.urlencode()
        return ctx
