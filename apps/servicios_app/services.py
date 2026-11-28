from django.db import transaction
from apps.asistencias_app.services import cerrar_vencidas
from .models import ServicioRealizado


class ServicioError(Exception):
    """Un error que se le muestra al administrador tal cual."""


@transaction.atomic
def cambiar_estado_realizado(realizado, activo):
    cerrar_vencidas()
    realizado = ServicioRealizado.objects.select_for_update().get(pk=realizado.pk)
    if not realizado.asistencia_en_curso:
        accion = "habilitar" if activo else "inhabilitar"
        raise ServicioError(
            f"No se puede {accion}: la asistencia de ese día ya tiene la salida registrada. "
            "Si es de hoy, reabrila primero."
        )
    realizado.activo = activo
    realizado.save(update_fields=["activo"])
    return realizado
