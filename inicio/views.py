from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from apps.empleados_app.models import Empleado
from apps.servicios_app.models import ServicioRealizado
from apps.asistencias_app.models import RegistroAsistencia
from apps.asistencias_app.services import cerrar_vencidas


@login_required
def home(request):

    cerrar_vencidas()
    hoy = timezone.localdate()
    if not request.user.is_superuser:
        return _home_empleado(request, hoy)
    return render(
        request,
        "inicio/home.html",
        {
            "empleados_activos": Empleado.objects.filter(activo=True).count(),
            "servicios_realizados_hoy": ServicioRealizado.objects.filter(activo=True, fecha_hora__date=hoy).count(),
            "asistencias_hoy": RegistroAsistencia.objects.filter(activo=True, fecha_hora_ingreso__date=hoy).count(),
            "ultimos_realizados": ServicioRealizado.objects.filter(activo=True).select_related(
                "empleado", "Registro_asistencia__empleado", "servicio"
            )[:5],
        },
    )


def _home_empleado(request, hoy):
    empleado = getattr(request.user, "empleado", None)
    contexto = {"empleado": empleado}
    if empleado:
        realizados = ServicioRealizado.objects.filter(activo=True, empleado=empleado)
        de_hoy = realizados.filter(fecha_hora__date=hoy)
        total = de_hoy.aggregate(total=Sum("monto_servicio"))["total"] or Decimal("0")
        contexto.update(
            servicios_hoy=de_hoy.count(),
            total_hoy=total.quantize(Decimal("0.01")),
            comision_hoy=(total * RegistroAsistencia.PORCENTAJE_COMISION).quantize(Decimal("0.01")),
            asistencia_hoy=empleado.asistencias.filter(
                activo=True, fecha_hora_ingreso__date=hoy
            ).first(),
            ultimos_realizados=realizados.select_related("servicio")[:5],
        )
    return render(request, "inicio/home_empleado.html", contexto)


def salud(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"estado": "no disponible"}, status=503)
    return JsonResponse({"estado": "ok"})
