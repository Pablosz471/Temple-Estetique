from django.db import transaction
from .models import ServicioRealizado


class ServicioError(Exception):
    """Un error que se le muestra al administrador tal cual."""


@transaction.atomic
def cambiar_estado_realizado(realizado, activo):
    realizado = ServicioRealizado.objects.select_for_update().get(pk=realizado.pk)
    if activo and not realizado.asistencia_en_curso:
        raise ServicioError(
            "No se puede habilitar: la asistencia de ese día no está en curso."
        )
    realizado.activo = activo
    realizado.save(update_fields=["activo"])
    return realizado
