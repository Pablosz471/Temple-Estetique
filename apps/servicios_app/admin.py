from django.contrib import admin
from .models import Servicio, ServicioRealizado

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_servicio", "descripcion", "precio", "activo")
    list_filter =("activo",)
    search_fields = ("nombre_servicio",)
    actions = ["inhabilitar", "habilitar"]

    def has_delete_permission(self, request, obj = None):
        return False

    @admin.action(description="Inhabilitar servicios seleccionados")
    def inhabilitar(self, request, queryset):
        cantidad=queryset.update(activo=False)
        self.message_user(request, f"{cantidad} servicio(s) inhabilitado(s).")

    @admin.action(description="Habilitar servicios seleccionados")
    def habilitar(self, request, queryset):
        cantidad=queryset.update(activo=True)
        self.message_user(request, f"{cantidad} servicio(s) habilitado(s).")

@admin.register(ServicioRealizado)
class ServicioRealizadoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "Registro_asistencia",
        "servicio",
        "fecha_hora",
        "monto_servicio",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
        "Registro_asistencia__empleado__nombre",
        "Registro_asistencia__empleado__apellido",
        "servicio__nombre_servicio",
    )
    list_filter = ("fecha_hora", "servicio")
    # El borrado masivo no pasa por ServicioRealizado.delete() y dejaría
    # comisiones diarias y totales mensuales desactualizados.
    actions = None
    
