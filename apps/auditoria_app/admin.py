from django.contrib import admin
from django.utils.text import Truncator
from .models import RegistroCambio


@admin.register(RegistroCambio)
class RegistroCambioAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "usuario_nombre", "accion", "modelo", "objeto", "resumen")
    list_filter = ("accion", "modelo", "fecha_hora")
    search_fields = ("usuario_nombre", "modelo", "objeto", "detalle")
    date_hierarchy = "fecha_hora"
    list_per_page = 50

    @admin.display(description="Detalle")
    def resumen(self, obj):
        return Truncator(obj.detalle).chars(80)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
