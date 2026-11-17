from django.contrib import admin
from .models import Servicio, ServicioRealizado

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_servicio", "descripcion", "precio")
    search_fields = ("nombre_servicio",)

@admin.register(ServicioRealizado)
class ServicioRealizadoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "Registro_asistencia",
        "servicio",
        "fecha",
        "monto_servicio",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
        "Registro_asistencia__empleado__nombre",
        "Registro_asistencia__empleado__apellido",
        "servicio__nombre_servicio",
    )
    list_filter = ("fecha", "servicio")
    
