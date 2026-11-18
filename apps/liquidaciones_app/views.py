from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from apps.empleados_app.models import Empleado
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
        hoy = timezone.localdate()
        # El mes en curso aparece siempre y con los números al día.
        RegistroMensual.actualizar(empleado.pk, hoy.year, hoy.month)
        todos = list(empleado.registros_mensuales.all())
        meses = [(r.clave, r.periodo) for r in todos]
        mes_elegido = request.GET.get("mes", "")
        if mes_elegido not in dict(meses):
            mes_elegido = ""
        registros = [r for r in todos if not mes_elegido or r.clave == mes_elegido]
        for registro in registros:
            registro.ultimos = list(registro.servicios()[:5])
            registro.cantidad = registro.servicios().count()
        contexto.update(
            empleado=empleado, registros=registros, meses=meses, mes_elegido=mes_elegido
        )
    return render(request, "liquidaciones/lista.html", contexto)


@login_required
def servicios_del_mes(request, pk):
    _exigir_admin(request)
    registro = get_object_or_404(RegistroMensual, pk=pk)
    registro = RegistroMensual.actualizar(registro.empleado_id, registro.anio, registro.mes)
    pagina = Paginator(registro.servicios(), 20).get_page(request.GET.get("page"))
    return render(
        request,
        "liquidaciones/servicios.html",
        {
            "registro": registro,
            "page_obj": pagina,
            "paginator": pagina.paginator,
            "is_paginated": pagina.has_other_pages(),
        },
    )
