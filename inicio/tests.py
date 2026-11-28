from django.urls import reverse
from apps.liquidaciones_app.models import RegistroMensual
from apps.pruebas import CLAVE, PruebaBase
from cuentas.models import Usuario

PANTALLAS_DE_ADMINISTRADOR = (
    "operaciones:servicios",
    "operaciones:servicio_crear",
    "operaciones:realizados",
    "operaciones:realizado_crear",
    "empleados:empleados",
    "empleados:empleado_crear",
    "asistencias:lista",
    "liquidaciones:lista",
    "auditoria:lista",
)
PANTALLAS_DE_EMPLEADO = (
    "asistencias:mis_asistencias",
    "liquidaciones:mis_liquidaciones",
)


class PermisosTests(PruebaBase):
    def setUp(self):
        self.admin = self.crear_empleado("jefa", "20111222", admin=True)
        self.ana = self.crear_empleado("ana", "30111222")

    def comprobar(self, nombres, estado):
        for nombre in nombres:
            with self.subTest(pantalla=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, estado)

    def test_sin_sesion_se_pide_ingresar(self):
        self.comprobar(PANTALLAS_DE_ADMINISTRADOR + PANTALLAS_DE_EMPLEADO, 302)

    def test_administrador(self):
        self.client.force_login(self.admin.usuario)
        self.comprobar(PANTALLAS_DE_ADMINISTRADOR, 200)
        self.comprobar(PANTALLAS_DE_EMPLEADO, 403)

    def test_empleado(self):
        self.client.force_login(self.ana.usuario)
        self.comprobar(PANTALLAS_DE_EMPLEADO, 200)
        self.comprobar(PANTALLAS_DE_ADMINISTRADOR, 403)
        for nombre in PANTALLAS_DE_EMPLEADO:
            self.assertEqual(self.client.post(reverse(nombre)).status_code, 405)

    def test_cuenta_sin_ficha_de_empleado(self):
        usuario = Usuario.objects.create_user(
            "sola", "sola@example.test", CLAVE, is_active=True, estado=Usuario.Estado.APROBADO
        )
        self.client.force_login(usuario)
        self.comprobar(PANTALLAS_DE_EMPLEADO, 403)
        self.assertContains(self.client.get(reverse("inicio:home")), "no tiene una ficha")


class InicioTests(PruebaBase):
    def setUp(self):
        self.ana = self.crear_empleado("ana", "30111222")
        self.bea = self.crear_empleado("bea", "31111222")
        self.propio = self.realizar(self.ana, "PROPIO", "1000", observacion="NOTA")
        self.realizar(self.ana, "ANULADO", "500", activo=False)
        self.ajeno = self.realizar(self.bea, "AJENO", "700")

    def test_el_empleado_ve_solo_lo_suyo(self):
        self.client.force_login(self.ana.usuario)
        respuesta = self.client.get(reverse("inicio:home"))
        self.assertContains(respuesta, "PROPIO")
        self.assertContains(respuesta, "ANULADO")
        self.assertContains(respuesta, "Inhabilitado")
        self.assertNotContains(respuesta, "AJENO")
        self.assertEqual(respuesta.context["servicios_hoy"], 1)
        self.assertEqual(str(respuesta.context["comision_hoy"]), "400.00")

    def test_el_administrador_cuenta_solo_registros_habilitados(self):
        self.client.force_login(self.crear_empleado("jefa", "20111222", admin=True).usuario)
        respuesta = self.client.get(reverse("inicio:home"))
        self.assertEqual(respuesta.context["servicios_realizados_hoy"], 2)

    def test_detalle_del_mes_propio_filtrado_y_sin_observaciones(self):
        propio = RegistroMensual.objects.get(empleado=self.ana)
        ajeno = RegistroMensual.objects.get(empleado=self.bea)
        self.client.force_login(self.ana.usuario)
        url = reverse("liquidaciones:mis_servicios_del_mes", args=[propio.pk])
        respuesta = self.client.get(url, {"servicio": self.ajeno.servicio_id})
        self.assertContains(respuesta, "PROPIO")
        self.assertNotContains(respuesta, "AJENO")
        self.assertContains(respuesta, "ANULADO")
        self.assertContains(respuesta, "<td>Inhabilitado</td>")
        self.assertNotContains(respuesta, "NOTA")
        otro = reverse("liquidaciones:mis_servicios_del_mes", args=[ajeno.pk])
        self.assertEqual(self.client.get(otro).status_code, 404)

    def test_los_inhabilitados_se_ven_pero_no_suman(self):
        self.client.force_login(self.ana.usuario)
        respuesta = self.client.get(reverse("liquidaciones:mis_liquidaciones"))
        registro = respuesta.context["registros"][0]
        self.assertContains(respuesta, "ANULADO")
        self.assertEqual(len(registro.ultimos), 2)
        self.assertEqual(registro.cantidad, 1)
        self.assertEqual(str(registro.total_generado), "1000.00")

        jefa = self.crear_empleado("jefa", "20111222", admin=True)
        self.client.force_login(jefa.usuario)
        url = reverse("liquidaciones:servicios", args=[registro.pk])
        self.assertNotContains(self.client.get(url), "ANULADO")

    def test_el_detalle_del_mes_muestra_la_comision_de_cada_servicio(self):
        registro = RegistroMensual.objects.get(empleado=self.ana)
        jefa = self.crear_empleado("jefa", "20111222", admin=True)
        for usuario, nombre in (
            (self.ana.usuario, "liquidaciones:mis_servicios_del_mes"),
            (jefa.usuario, "liquidaciones:servicios"),
        ):
            self.client.force_login(usuario)
            respuesta = self.client.get(reverse(nombre, args=[registro.pk]))
            self.assertContains(respuesta, "Comisión (40%)</th>")
            self.assertContains(respuesta, "<td>$ 400,00</td>")

    def test_la_lista_de_servicios_tiene_una_columna_por_dato(self):
        self.client.force_login(self.crear_empleado("jefa", "20111222", admin=True).usuario)
        for nombre in ("operaciones:servicios", "operaciones:realizados"):
            respuesta = self.client.get(reverse(nombre))
            for fila in respuesta.context["filas"]:
                self.assertEqual(len(fila["valores"]), len(respuesta.context["columnas"]))
