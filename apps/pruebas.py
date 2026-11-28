"""Datos y configuración compartidos por las pruebas."""

from decimal import Decimal
from django.test import TestCase, override_settings
from django.utils import timezone
from apps.empleados_app.models import Empleado, Rol
from apps.servicios_app.models import Servicio, ServicioRealizado
from cuentas.models import Usuario

CLAVE = "Temporal-segura-298!"


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    },
)
class PruebaBase(TestCase):
    def crear_empleado(self, nombre, dni, admin=False):
        usuario = Usuario.objects.create_user(
            nombre, f"{nombre}@example.test", CLAVE,
            is_active=True, estado=Usuario.Estado.APROBADO,
        )
        rol = Rol.objects.get(nombre_rol=Rol.ADMINISTRADOR if admin else Rol.EMPLEADO)
        return Empleado.objects.create(
            usuario=usuario, rol=rol, nombre=nombre, apellido="Prueba",
            dni=dni, telefono="3871234567",
        )

    def realizar(self, empleado, nombre, monto, activo=True, **campos):
        servicio = Servicio.objects.create(
            nombre_servicio=nombre, descripcion="Prueba", precio=Decimal(monto)
        )
        return ServicioRealizado.objects.create(
            empleado=empleado, servicio=servicio, fecha_hora=timezone.now(),
            monto_servicio=Decimal(monto), activo=activo, **campos,
        )
