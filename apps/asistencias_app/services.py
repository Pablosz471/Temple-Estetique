"""Ingreso, salida y cierre automático de asistencias."""

from datetime import datetime, time
from django.db import transaction
from django.utils import timezone
from apps.empleados_app.models import Empleado
from .models import RegistroAsistencia

HORA_CIERRE = time(23, 59)


class AsistenciaError(Exception):
    """Un error que se le muestra al administrador tal cual."""


def _cierre_del_dia(ingreso):
    dia = timezone.localtime(ingreso).date()
    cierre = timezone.make_aware(datetime.combine(dia, HORA_CIERRE))
    return max(cierre, ingreso)


def _cerrar(asistencia, momento):
    asistencia.fecha_hora_salida = momento
    asistencia.comision_diaria = asistencia.calcular_comision()
    asistencia.save(update_fields=["fecha_hora_salida", "comision_diaria"])


@transaction.atomic
def cerrar_vencidas():
    ahora = timezone.now()
    abiertas = RegistroAsistencia.objects.select_for_update(skip_locked=True).filter(
        fecha_hora_salida__isnull=True
    )
    for asistencia in abiertas:
        cierre = _cierre_del_dia(asistencia.fecha_hora_ingreso)
        if ahora >= cierre:
            _cerrar(asistencia, cierre)


@transaction.atomic
def registrar_ingreso(empleado):
    cerrar_vencidas()
    empleado = Empleado.objects.select_for_update().get(pk=empleado.pk)
    if empleado.asistencias.filter(fecha_hora_ingreso__date=timezone.localdate()).exists():
        raise AsistenciaError(f"{empleado} ya registró su asistencia hoy.")
    return RegistroAsistencia.objects.create(
        empleado=empleado, fecha_hora_ingreso=timezone.now()
    )


@transaction.atomic
def registrar_salida(empleado):
    asistencia = (
        RegistroAsistencia.objects.select_for_update()
        .filter(empleado=empleado, fecha_hora_salida__isnull=True)
        .first()
    )
    if asistencia is None:
        raise AsistenciaError(f"{empleado} no tiene una asistencia en curso.")
    cierre = _cierre_del_dia(asistencia.fecha_hora_ingreso)
    _cerrar(asistencia, min(timezone.now(), cierre))
    return asistencia
