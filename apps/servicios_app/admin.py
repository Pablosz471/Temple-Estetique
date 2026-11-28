from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from .forms import EditarRealizadoForm, RegistrarServicioForm
from .models import Servicio, ServicioRealizado
from .services import ServicioError, cambiar_estado_realizado


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
        cantidad = 0
        for servicio in queryset.filter(activo=True):
            servicio.activo = False
            servicio.save(update_fields=["activo"])
            cantidad += 1
        self.message_user(request, f"{cantidad} servicio(s) inhabilitado(s).")

    @admin.action(description="Habilitar servicios seleccionados")
    def habilitar(self, request, queryset):
        cantidad = 0
        for servicio in queryset.filter(activo=False):
            servicio.activo = True
            try:
                servicio.clean()
            except ValidationError:
                self.message_user(
                    request,
                    f"{servicio}: ya existe un servicio habilitado con ese nombre.",
                    messages.WARNING,
                )
                continue
            servicio.save(update_fields=["activo"])
            cantidad += 1
        self.message_user(request, f"{cantidad} servicio(s) habilitado(s).")


@admin.register(ServicioRealizado)
class ServicioRealizadoAdmin(admin.ModelAdmin):
    list_display = ("id", "empleado", "Registro_asistencia", "servicio", "fecha_hora", "monto_servicio", "activo",)
    search_fields = ("empleado__nombre", "empleado__apellido", "Registro_asistencia__empleado__nombre", "Registro_asistencia__empleado__apellido", "servicio__nombre_servicio",)
    list_filter = ("fecha_hora", "servicio", "activo")
    actions = ["inhabilitar", "habilitar"]

    def get_fields(self, request, obj=None):
        if obj is None:
            return ["empleado", "servicio", "observacion"]
        return ["empleado", "Registro_asistencia", "fecha_hora", "monto_servicio",
                "servicio", "observacion", "activo"]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        return ["empleado", "Registro_asistencia", "fecha_hora", "monto_servicio", "activo"]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = RegistrarServicioForm if obj is None else EditarRealizadoForm
        return super().get_form(request, obj, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None:
            en_curso = obj.asistencia_en_curso
            extra_context["puede_inhabilitar"] = obj.activo and en_curso
            extra_context["puede_habilitar"] = (not obj.activo) and en_curso
            extra_context["show_save"] = en_curso
            extra_context["show_save_and_continue"] = en_curso
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        for clave, activo in (("_inhabilitar", False), ("_habilitar", True)):
            if clave in request.POST:
                try:
                    cambiar_estado_realizado(obj, activo)
                    self.message_user(request, "Servicio realizado actualizado.")
                except ServicioError as error:
                    self.message_user(request, str(error), messages.ERROR)
                return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    def _cambiar_estado(self, request, queryset, activo):
        cambiados = 0
        for realizado in queryset:
            if realizado.activo == activo:
                continue
            try:
                cambiar_estado_realizado(realizado, activo)
                cambiados += 1
            except ServicioError as error:
                self.message_user(request, f"{realizado}: {error}", messages.WARNING)
        return cambiados

    @admin.action(description="Inhabilitar servicios realizados seleccionados")
    def inhabilitar(self, request, queryset):
        n = self._cambiar_estado(request, queryset, False)
        self.message_user(request, f"{n} servicio(s) realizado(s) inhabilitado(s).")

    @admin.action(description="Habilitar servicios realizados seleccionados")
    def habilitar(self, request, queryset):
        n = self._cambiar_estado(request, queryset, True)
        self.message_user(request, f"{n} servicio(s) realizado(s) habilitado(s).")

