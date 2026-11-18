from datetime import datetime
from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from apps.empleados_app.models import Empleado, Rol
from apps.servicios_app.models import Servicio, ServicioRealizado
from cuentas.models import Usuario
from .models import RegistroMensual


def local(anio, mes, dia, hora=12, minuto=0):
    """Una fecha y hora en la zona horaria del salón (America/Argentina/Salta)."""
    return timezone.make_aware(datetime(anio, mes, dia, hora, minuto))


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    },
)
class LiquidacionesTests(TestCase):
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

    def registrar(self, monto, fecha_hora):
        return ServicioRealizado.objects.create(
            empleado=self.empleado,
            servicio=self.facial,
            fecha_hora=fecha_hora,
            monto_servicio=Decimal(monto),
        )

    def registro(self, anio, mes):
        return RegistroMensual.objects.get(empleado=self.empleado, anio=anio, mes=mes)

    def test_registrar_servicio_suma_al_mes_y_calcula_40(self):
        self.registrar("10000", local(2026, 11, 3))
        self.registrar("5000", local(2026, 11, 20))
        registro = self.registro(2026, 11)
        self.assertEqual(registro.total_generado, Decimal("15000.00"))
        self.assertEqual(registro.total_comisiones, Decimal("6000.00"))

    def test_borrar_servicio_resta_del_mes(self):
        self.registrar("10000", local(2026, 11, 3))
        segundo = self.registrar("5000", local(2026, 11, 4))
        segundo.delete()
        registro = self.registro(2026, 11)
        self.assertEqual(registro.total_generado, Decimal("10000.00"))
        self.assertEqual(registro.total_comisiones, Decimal("4000.00"))

    def test_cada_mes_tiene_su_propio_registro(self):
        self.registrar("10000", local(2026, 10, 15))
        self.registrar("2000", local(2026, 11, 2))
        self.assertEqual(self.registro(2026, 10).total_generado, Decimal("10000.00"))
        self.assertEqual(self.registro(2026, 11).total_generado, Decimal("2000.00"))

    def test_el_mes_se_decide_en_hora_argentina(self):
        # 31/10 a las 23:30 en Salta ya es 1/11 en UTC, pero cuenta para octubre.
        self.registrar("7000", local(2026, 10, 31, 23, 30))
        self.assertEqual(self.registro(2026, 10).total_generado, Decimal("7000.00"))
        self.assertFalse(
            RegistroMensual.objects.filter(empleado=self.empleado, anio=2026, mes=11).exists()
        )

    def test_operador_no_puede_ver_liquidaciones(self):
        self.client.force_login(self.empleado.usuario)
        self.assertEqual(self.client.get(reverse("liquidaciones:lista")).status_code, 403)

    def test_sin_empleado_pide_elegir_uno(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("liquidaciones:lista")), "Elegí un empleado")

    def test_mes_en_curso_aparece_aunque_este_en_cero(self):
        self.client.force_login(self.admin)
        hoy = timezone.localdate()
        respuesta = self.client.get(reverse("liquidaciones:lista"), {"empleado": self.empleado.pk})
        self.assertContains(respuesta, "En curso")
        self.assertContains(respuesta, "Todavía no hay servicios realizados en este mes")
        self.assertEqual(self.registro(hoy.year, hoy.month).total_generado, Decimal("0.00"))

    def test_filtrar_por_mes_muestra_solo_ese_registro(self):
        self.registrar("10000", local(2025, 3, 10))
        self.registrar("2000", local(2025, 4, 10))
        self.client.force_login(self.admin)
        respuesta = self.client.get(
            reverse("liquidaciones:lista"), {"empleado": self.empleado.pk, "mes": "2025-03"}
        )
        registros = respuesta.context["registros"]
        self.assertEqual([r.clave for r in registros], ["2025-03"])

    def test_mes_inexistente_muestra_todos_los_meses(self):
        self.registrar("10000", local(2025, 3, 10))
        self.client.force_login(self.admin)
        respuesta = self.client.get(
            reverse("liquidaciones:lista"), {"empleado": self.empleado.pk, "mes": "1999-01"}
        )
        self.assertEqual(respuesta.context["mes_elegido"], "")
        self.assertIn("2025-03", [r.clave for r in respuesta.context["registros"]])

    def test_ultimos_cinco_y_ver_mas_con_todos(self):
        for dia in range(1, 8):
            self.registrar("1000", local(2025, 5, dia))
        self.client.force_login(self.admin)
        respuesta = self.client.get(
            reverse("liquidaciones:lista"), {"empleado": self.empleado.pk, "mes": "2025-05"}
        )
        registro = respuesta.context["registros"][0]
        self.assertEqual(len(registro.ultimos), 5)
        self.assertEqual(registro.cantidad, 7)
        self.assertEqual(registro.ultimos[0].fecha_hora, local(2025, 5, 7))
        detalle = self.client.get(reverse("liquidaciones:servicios", args=[registro.pk]))
        self.assertEqual(detalle.context["paginator"].count, 7)
        self.assertContains(detalle, "Volver a las liquidaciones")
