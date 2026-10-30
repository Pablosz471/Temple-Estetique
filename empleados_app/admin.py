from django.contrib import admin
from .models import Rol, Empleado

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombreRol", "descripcion")
    search_fields = ("nombre_rol",)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "dni", "rol", "estado")
    search_fields = ("nombre", "apellido", "dni")
    list_filter = ("rol", "estado")