from django.contrib import admin
from .models import RegistroMensual, Aguinaldo

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

@admin.register(Aguinaldo)
class AguinaldoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "semestre",
        "anio",
        "mejor_sueldo_semestre",
        "monto_aguinaldo",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
    )
    list_filter = ("semestre", "anio")