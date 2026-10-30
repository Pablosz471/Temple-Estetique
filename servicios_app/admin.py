from django.contrib import admin
from .models import Servicio, ServicioRealizado

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_servicio", "descripcion")
    search_fields = ("nombre_servicio",)

@admin.register(ServicioRealizado)
class ServicioRealizadoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "servicio",
        "fecha",
        "monto_servicio",
        "porcentaje_empleado",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
        "servicio__nombre_servicio",
    )
    list_filter = ("fecha", "servicio")
    
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
        "servicio__nombre_servicio",
    )
    list_filter = ("fecha", "servicio")
    