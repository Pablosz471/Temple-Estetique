from django.conf import settings
from apps.asistencias_app.models import RegistroAsistencia


def organizacion(request):
    return {"organizacion_nombre": settings.SITE_NAME}


def comision(request):
    return {"porcentaje_comision": int(RegistroAsistencia.PORCENTAJE_COMISION * 100)}
