from datetime import date
from django.db.models import Q


def _a_fecha(texto):
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


class ListadoMixin:
    """Búsqueda, filtros, rango de fechas y orden para las listas.

    ordenes:  ((clave, etiqueta, campos), ...); la primera es la predeterminada.
    filtros:  ({"param", "etiqueta", "campo", "opciones"}, ...) donde opciones es una 
    lista (o función que la devuelve) de (valor_en_url, etiqueta, valor_a_filtrar).
    campo_fecha: campo de fecha y hora sobre el que se aplica el rango desde/hasta.
    """

    busqueda = ()
    ordenes = ()
    filtros = ()
    campo_fecha = None
    etiqueta_fecha = "Fecha"

    def _filtros_resueltos(self):
        if not hasattr(self, "_filtros_cache"):
            self._filtros_cache = [
                (f, list(f["opciones"]() if callable(f["opciones"]) else f["opciones"]))
                for f in self.filtros
            ]
        return self._filtros_cache

    def _orden_actual(self):
        claves = [clave for clave, _etiqueta, _campos in self.ordenes]
        pedido = self.request.GET.get("orden", "")
        return pedido if pedido in claves else (claves[0] if claves else "")

    def get_queryset(self):
        qs = super().get_queryset()
        get = self.request.GET

        termino = get.get("q", "").strip()[:100]
        if termino and self.busqueda:
            condicion = Q()
            for campo in self.busqueda:
                condicion |= Q(**{f"{campo}__icontains": termino})
            qs = qs.filter(condicion)

        for filtro, opciones in self._filtros_resueltos():
            elegido = get.get(filtro["param"], "")
            for valor, _etiqueta, valor_filtro in opciones:
                if valor == elegido:
                    qs = qs.filter(**{filtro["campo"]: valor_filtro})
                    break

        if self.campo_fecha:
            desde = _a_fecha(get.get("desde", ""))
            hasta = _a_fecha(get.get("hasta", ""))
            if desde:
                qs = qs.filter(**{f"{self.campo_fecha}__date__gte": desde})
            if hasta:
                qs = qs.filter(**{f"{self.campo_fecha}__date__lte": hasta})

        if self.ordenes:
            actual = self._orden_actual()
            campos = next(c for clave, _e, c in self.ordenes if clave == actual)
            qs = qs.order_by(*campos, "pk")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        get = self.request.GET

        actual = self._orden_actual()
        ctx["orden_opciones"] = [
            {"clave": clave, "etiqueta": etiqueta, "activa": clave == actual}
            for clave, etiqueta, _campos in self.ordenes
        ]
        ctx["filtros_ui"] = [
            {
                "param": filtro["param"],
                "etiqueta": filtro["etiqueta"],
                "opciones": [
                    {"valor": valor, "etiqueta": etiqueta, "activa": valor == get.get(filtro["param"], "")}
                    for valor, etiqueta, _filtrar in opciones
                ],
            }
            for filtro, opciones in self._filtros_resueltos()
        ]
        ctx["fecha_ui"] = (
            {
                "etiqueta": self.etiqueta_fecha,
                "desde": get.get("desde", ""),
                "hasta": get.get("hasta", ""),
            }
            if self.campo_fecha
            else None
        )
        parametros = get.copy()
        parametros.pop("page", None)
        ctx["querystring"] = parametros.urlencode()

        activos = sum(
            1 for f in ctx["filtros_ui"] if any(o["activa"] for o in f["opciones"])
        )
        if ctx["fecha_ui"]:
            activos += bool(ctx["fecha_ui"]["desde"]) + bool(ctx["fecha_ui"]["hasta"])
        ctx["filtros_activos"] = activos
        ctx["hay_criterios"] = bool(get.get("q", "").strip() or activos or get.get("orden"))

        return ctx
