from django.contrib import admin, messages
from .forms import EmpleadoCrearForm, EmpleadoEditarForm
from .models import Rol, Empleado, HistorialAcceso


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_rol", "descripcion")
    search_fields = ("nombre_rol",)
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "dni", "rol", "activo")
    search_fields = ("nombre", "apellido", "dni")
    list_filter = ("rol", "activo")
    actions = ["inhabilitar", "habilitar"]
    readonly_fields = ("usuario_asociado",)

    def get_fields(self, request, obj=None):
        if obj is None:
            return ["username", "nombre", "apellido", "dni", "telefono", "email", "rol", "direccion", "password1", "password2"]
        return ["usuario_asociado", "nombre", "apellido", "dni", "telefono", "email", "rol", "activo", "direccion"]

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = EmpleadoCrearForm
            return super().get_form(request, obj, **kwargs)
        kwargs["form"] = EmpleadoEditarForm
        Form = super().get_form(request, obj, **kwargs)
        usuario = request.user

        class FormEdicion(Form):
            def __init__(self, *args, **kw):
                super().__init__(*args, usuario_actual=usuario, **kw)

        return FormEdicion

    @admin.display(description="Usuario")
    def usuario_asociado(self, obj):
        return obj.usuario.username

    def has_delete_permission(self, request, obj=None):
        return False

    def _cambiar_estado(self, request, queryset, activo):
        cambiados = 0
        for empleado in queryset.select_related("usuario"):
            if not activo and empleado.usuario_id == request.user.pk:
                self.message_user(request, "No podés inhabilitar tu propio perfil.", messages.ERROR)
                continue
            if empleado.activo != activo:
                empleado.activo = activo
                empleado.save()
                cambiados += 1
        return cambiados

    @admin.action(description="Inhabilitar empleados seleccionados")
    def inhabilitar(self, request, queryset):
        n = self._cambiar_estado(request, queryset, False)
        self.message_user(request, f"{n} empleado(s) inhabilitado(s).")

    @admin.action(description="Habilitar empleados seleccionados")
    def habilitar(self, request, queryset):
        n = self._cambiar_estado(request, queryset, True)
        self.message_user(request, f"{n} empleado(s) habilitado(s).")


@admin.register(HistorialAcceso)
class HistorialAccesoAdmin(admin.ModelAdmin):
    list_display = ("id", "email_ingresado", "empleado", "fecha_hora", "resultado",)
    list_filter = ("resultado", "fecha_hora")
    search_fields = ("email_ingresado",)
    