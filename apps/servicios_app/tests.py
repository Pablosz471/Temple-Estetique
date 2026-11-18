from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.asistencias_app.services import registrar_ingreso, registrar_salida
from apps.empleados_app.models import Empleado, Rol
from cuentas.models import Usuario
from .forms import RegistrarServicioForm
from .models import Servicio, ServicioRealizado


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    },
)
class RegistrarServicioTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            "admin", "admin@example.test", "Temporal-segura-298!"
        )
        cuenta = Usuario.objects.create_user(
            "maria", "maria@example.test", "Temporal-segura-298!",
            is_active=True, estado=Usuario.Estado.APROBADO,
        )
        self.empleado = Empleado.objects.create(
            usuario=cuenta,
            rol=Rol.objects.get(nombre_rol=Rol.EMPLEADO),
            nombre="María",
            apellido="López",
            dni="30111222",
            telefono="3871234567",
        )
        self.facial = Servicio.objects.create(
            nombre_servicio="Limpieza facial", descripcion="Prueba", precio=Decimal("8000")
        )

    def opciones(self):
        return list(RegistrarServicioForm().fields["empleado"].queryset)

    def test_empleado_sin_asistencias_no_aparece(self):
        self.assertEqual(self.opciones(), [])

    def test_empleado_con_asistencia_en_curso_aparece(self):
        registrar_ingreso(self.empleado)
        self.assertEqual(self.opciones(), [self.empleado])

    def test_empleado_con_salida_registrada_no_aparece(self):
        registrar_ingreso(self.empleado)
        registrar_salida(self.empleado)
        self.assertEqual(self.opciones(), [])

    def test_empleado_con_asistencia_borrada_no_aparece(self):
        # El caso reportado: ingreso, salida y después se borra la asistencia.
        asistencia = registrar_ingreso(self.empleado)
        registrar_salida(self.empleado)
        asistencia.delete()
        self.assertEqual(self.opciones(), [])

    def test_enviar_empleado_sin_asistencia_muestra_error_y_no_guarda(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("operaciones:realizado_crear"),
            {"empleado": self.empleado.pk, "servicio": self.facial.pk},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].errors)
        self.assertFalse(ServicioRealizado.objects.exists())

    def test_registrar_toma_precio_y_asistencia_abierta(self):
        asistencia = registrar_ingreso(self.empleado)
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("operaciones:realizado_crear"),
            {"empleado": self.empleado.pk, "servicio": self.facial.pk, "observacion": ""},
        )
        self.assertRedirects(respuesta, reverse("operaciones:realizados"))
        realizado = ServicioRealizado.objects.get()
        self.assertEqual(realizado.monto_servicio, Decimal("8000.00"))
        self.assertEqual(realizado.Registro_asistencia, asistencia)
        self.assertEqual(realizado.empleado, self.empleado)
