from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from apps.pruebas import PruebaBase
from apps.servicios_app.models import Servicio, ServicioRealizado
from .models import RegistroAsistencia
from .services import cerrar_vencidas, registrar_ingreso, registrar_salida


class AsistenciasTests(PruebaBase):
    def setUp(self):
        self.admin = self.crear_empleado("jefa", "20111222", admin=True)
        self.ana = self.crear_empleado("ana", "30111222")
        self.client.force_login(self.admin.usuario)

    def marcar(self, accion):
        return self.client.post(
            reverse("asistencias:marcar"),
            {"empleado": self.ana.pk, "accion": accion},
            follow=True,
        )

    def test_ingreso_salida_y_reapertura(self):
        self.marcar("ingreso")
        asistencia = RegistroAsistencia.objects.get()
        self.assertTrue(asistencia.abierta)

        self.realizar(self.ana, "Corte", "1000", Registro_asistencia=asistencia)
        self.marcar("salida")
        asistencia.refresh_from_db()
        self.assertFalse(asistencia.abierta)
        self.assertEqual(asistencia.comision_diaria, Decimal("400.00"))

        self.marcar("reabrir")
        asistencia.refresh_from_db()
        self.assertTrue(asistencia.abierta)

    def test_una_sola_asistencia_por_dia(self):
        self.marcar("ingreso")
        self.marcar("salida")
        respuesta = self.marcar("ingreso")
        self.assertContains(respuesta, "ya registró su asistencia hoy")
        self.assertEqual(RegistroAsistencia.objects.count(), 1)

    def test_no_se_inhabilita_una_asistencia_en_curso(self):
        asistencia = registrar_ingreso(self.ana)
        self.client.post(reverse("asistencias:estado", args=[asistencia.pk]))
        asistencia.refresh_from_db()
        self.assertTrue(asistencia.activo)

    def test_no_se_inhabilita_con_servicios_realizados(self):
        asistencia = registrar_ingreso(self.ana)
        self.realizar(self.ana, "Corte", "1000", Registro_asistencia=asistencia)
        registrar_salida(self.ana)
        self.client.post(reverse("asistencias:estado", args=[asistencia.pk]))
        asistencia.refresh_from_db()
        self.assertTrue(asistencia.activo)

    def test_inhabilitar_permite_un_nuevo_ingreso(self):
        asistencia = registrar_ingreso(self.ana)
        registrar_salida(self.ana)
        self.client.post(reverse("asistencias:estado", args=[asistencia.pk]))
        asistencia.refresh_from_db()
        self.assertFalse(asistencia.activo)
        registrar_ingreso(self.ana)
        self.assertEqual(RegistroAsistencia.objects.filter(activo=True).count(), 1)

    def test_las_asistencias_vencidas_se_cierran_solas(self):
        ayer = timezone.now() - timedelta(days=1)
        asistencia = RegistroAsistencia.objects.create(empleado=self.ana, fecha_hora_ingreso=ayer)
        cerrar_vencidas()
        asistencia.refresh_from_db()
        cierre = timezone.localtime(asistencia.fecha_hora_salida)
        self.assertEqual((cierre.hour, cierre.minute), (23, 59))
        self.assertEqual(cierre.date(), timezone.localtime(ayer).date())

    def test_hasta_las_23_59_se_registra_con_la_fecha_del_dia(self):
        servicio = Servicio.objects.create(
            nombre_servicio="Corte", descripcion="Prueba", precio=Decimal("1000")
        )
        datos = {"empleado": self.ana.pk, "servicio": servicio.pk}
        url = reverse("operaciones:realizado_crear")
        noche = timezone.make_aware(datetime(2026, 3, 10, 23, 59, 30))

        with patch("django.utils.timezone.now", return_value=noche):
            self.client.force_login(self.admin.usuario)
            asistencia = registrar_ingreso(self.ana)
            self.client.post(url, datos)
            cerrar_vencidas()
        asistencia.refresh_from_db()
        self.assertTrue(asistencia.abierta)
        self.assertEqual(str(asistencia), "ana Prueba - 10/03/2026")
        self.assertEqual(timezone.localtime(ServicioRealizado.objects.get().fecha_hora), noche)

        # Pasada la medianoche ya no se puede cargar nada en la jornada anterior.
        with patch("django.utils.timezone.now", return_value=noche + timedelta(minutes=1)):
            respuesta = self.client.post(url, datos)
        self.assertTrue(respuesta.context["form"].errors)
        self.assertEqual(ServicioRealizado.objects.count(), 1)
        asistencia.refresh_from_db()
        salida = timezone.localtime(asistencia.fecha_hora_salida)
        self.assertEqual((salida.day, salida.hour, salida.minute), (10, 23, 59))
        self.assertEqual(asistencia.comision_diaria, Decimal("400.00"))

    def test_la_lista_muestra_acciones_y_estado(self):
        registrar_ingreso(self.ana)
        respuesta = self.client.get(reverse("asistencias:lista"))
        fila = respuesta.context["filas"][0]
        self.assertEqual(len(fila["valores"]), len(respuesta.context["columnas"]))
        self.assertContains(respuesta, "En curso")
        self.assertContains(respuesta, "Inhabilitar")
        self.assertNotContains(respuesta, "Nuevo registro")

    def test_el_empleado_ve_solo_sus_asistencias_habilitadas(self):
        bea = self.crear_empleado("bea", "31111222")
        ahora = timezone.now()
        for empleado, detalle, dias, activo in (
            (self.ana, "PROPIA", 1, True),
            (self.ana, "ANULADA", 2, False),
            (bea, "AJENA", 1, True),
        ):
            momento = ahora - timedelta(days=dias)
            RegistroAsistencia.objects.create(
                empleado=empleado, fecha_hora_ingreso=momento,
                fecha_hora_salida=momento, detalle=detalle, activo=activo,
            )
        self.client.force_login(self.ana.usuario)
        respuesta = self.client.get(reverse("asistencias:mis_asistencias"), {"empleado": bea.pk})
        self.assertContains(respuesta, "PROPIA")
        self.assertNotContains(respuesta, "ANULADA")
        self.assertNotContains(respuesta, "AJENA")
        self.assertNotContains(respuesta, "Acciones")
