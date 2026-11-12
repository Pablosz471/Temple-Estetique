from django.contrib import admin
from .models import Rol, Empleado, HistorialAcceso

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_rol", "descripcion")
    search_fields = ("nombre_rol",)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "dni", "rol", "estado")
    search_fields = ("nombre", "apellido", "dni")
    list_filter = ("rol", "estado")

@admin.register(HistorialAcceso)
class HistorialAccesoAdmin(admin.ModelAdmin):
    list_display = ("id", "email_ingresado", "empleado", "fecha_hora", "resultado",)
    list_filter = ("resultado", "fecha_hora")
    search_fields = ("email_ingresado",)
    