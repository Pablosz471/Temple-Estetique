from django.contrib import admin
from .models import RegistroMensual

@admin.register(RegistroMensual)
class RegistroMensualAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "mes",
        "anio",
        "total_generado",
        "total_porcentaje",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
    )
    list_filter = ("mes", "anio")

