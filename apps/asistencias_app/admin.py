from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from .forms import IngresoAsistenciaForm
from .models import RegistroAsistencia
from .services import (
    AsistenciaError,
    cambiar_estado_asistencia,
    reabrir_asistencia,
    registrar_salida,
    tiene_otra_activa,
    tiene_servicios,
)


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "empleado", "fecha_hora_ingreso", "fecha_hora_salida", "comision_diaria", "activo")
    search_fields = ("empleado__nombre", "empleado__apellido")
    list_filter = ("fecha_hora_ingreso", "activo")
    actions = ["inhabilitar", "habilitar"]

    def get_fields(self, request, obj=None):
        if obj is None:
            return ["empleado"]
        return ["empleado", "fecha_hora_ingreso", "fecha_hora_salida", "comision_diaria", "activo", "detalle"]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        return ["empleado", "fecha_hora_ingreso", "fecha_hora_salida", "comision_diaria", "activo"]

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = IngresoAsistenciaForm
        return super().get_form(request, obj, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.fecha_hora_ingreso = timezone.now()
        super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None:
            es_de_hoy = timezone.localtime(obj.fecha_hora_ingreso).date() == timezone.localdate()
            extra_context["puede_reabrir"] = obj.activo and (not obj.abierta) and es_de_hoy
            extra_context["puede_inhabilitar"] = (
                obj.activo and not obj.abierta and not tiene_servicios(obj)
            )
            extra_context["puede_habilitar"] = (not obj.activo) and not tiene_otra_activa(obj)
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        acciones = {
            "_salida": lambda: registrar_salida(obj.empleado),
            "_reabrir": lambda: reabrir_asistencia(obj.empleado),
            "_inhabilitar": lambda: cambiar_estado_asistencia(obj, False),
            "_habilitar": lambda: cambiar_estado_asistencia(obj, True),
        }
        for clave, accion in acciones.items():
            if clave in request.POST:
                try:
                    accion()
                    self.message_user(request, "Asistencia actualizada.")
                except AsistenciaError as error:
                    self.message_user(request, str(error), messages.ERROR)
                return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    def _cambiar_estado(self, request, queryset, activo):
        cambiadas = 0
        for asistencia in queryset.select_related("empleado"):
            if asistencia.activo == activo:
                continue
            try:
                cambiar_estado_asistencia(asistencia, activo)
                cambiadas += 1
            except AsistenciaError as error:
                self.message_user(request, f"{asistencia}: {error}", messages.WARNING)
        return cambiadas

    @admin.action(description="Inhabilitar asistencias seleccionadas")
    def inhabilitar(self, request, queryset):
        n = self._cambiar_estado(request, queryset, False)
        self.message_user(request, f"{n} asistencia(s) inhabilitada(s).")

    @admin.action(description="Habilitar asistencias seleccionadas")
    def habilitar(self, request, queryset):
        n = self._cambiar_estado(request, queryset, True)
        self.message_user(request, f"{n} asistencia(s) habilitada(s).")
