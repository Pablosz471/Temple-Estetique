from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.asistencias_app.services import reabrir_asistencia, registrar_ingreso, registrar_salida
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

    def crear_servicio(self, nombre):
        self.client.force_login(self.admin)
        return self.client.post(
            reverse("operaciones:servicio_crear"),
            {"nombre_servicio": nombre, "descripcion": "Prueba", "precio": "100"},
        )

    def test_no_se_repite_el_nombre_de_un_servicio_habilitado(self):
        respuesta = self.crear_servicio("  LIMPIEZA FACIAL ")
        self.assertContains(respuesta, "Ya existe un servicio habilitado con ese nombre.")
        self.assertEqual(Servicio.objects.count(), 1)

    def test_se_repite_el_nombre_de_un_servicio_inhabilitado(self):
        url = reverse("operaciones:servicio_eliminar", args=[self.facial.pk])
        self.client.force_login(self.admin)
        self.client.post(url)
        self.assertRedirects(
            self.crear_servicio("Limpieza facial"), reverse("operaciones:servicios")
        )
        # El anterior ya no se puede volver a habilitar mientras el nuevo lo esté.
        respuesta = self.client.post(url, follow=True)
        self.assertContains(respuesta, "No se puede habilitar")
        self.facial.refresh_from_db()
        self.assertFalse(self.facial.activo)

    def test_solo_se_inhabilita_un_realizado_con_la_asistencia_en_curso(self):
        asistencia = registrar_ingreso(self.empleado)
        realizado = ServicioRealizado.objects.create(
            empleado=self.empleado, Registro_asistencia=asistencia, servicio=self.facial,
            fecha_hora=asistencia.fecha_hora_ingreso, monto_servicio=Decimal("8000"),
        )
        registrar_salida(self.empleado)
        self.client.force_login(self.admin)
        url = reverse("operaciones:realizado_estado", args=[realizado.pk])

        respuesta = self.client.post(url, follow=True)
        self.assertContains(respuesta, "No se puede inhabilitar")
        realizado.refresh_from_db()
        self.assertTrue(realizado.activo)

        reabrir_asistencia(self.empleado)
        self.client.post(url)
        realizado.refresh_from_db()
        self.assertFalse(realizado.activo)

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
