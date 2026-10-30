from django.contrib import admin
from .models import RegistroAsistencia

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "fecha_hora_ingreso",
        "fecha_hora_salida",
        "sueldo_diario",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
    )
    list_filter = ("fecha_hora_ingreso",)