from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from apps.empleados_app.models import Empleado
from apps.servicios_app.models import Servicio, ServicioRealizado
from apps.asistencias_app.models import RegistroAsistencia
from apps.liquidaciones_app.models import RegistroMensual
from cuentas.models import Usuario


@login_required
def home(request):
    hoy = timezone.localdate()
    return render(
        request,
        "inicio/home.html",
        {
            "pendientes": (
                Usuario.objects.filter(estado="pendiente").count()
                if request.user.is_superuser
                else None
            ),
            "empleados_activos": Empleado.objects.filter(estado="Activo").count(),
            "servicios_activos": Servicio.objects.count(),
            "asistencias_hoy": RegistroAsistencia.objects.filter(fecha_hora_ingreso__date=hoy).count(),
            "liquidaciones_mes": RegistroMensual.objects.filter(mes=hoy.month, anio=hoy.year).count(),
            "ultimos_realizados": ServicioRealizado.objects.select_related(
                "empleado", "Registro_asistencia__empleado", "servicio"
            )[:5],
        },
    )


def salud(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"estado": "no disponible"}, status=503)
    return JsonResponse({"estado": "ok"})
