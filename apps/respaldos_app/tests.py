import tempfile
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.db import connection
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.auditoria_app.models import RegistroCambio
from apps.pruebas import PruebaBase
from . import services
from .management.commands.backup_automatico import Command


class RespaldosTests(PruebaBase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = Path(temporal.name)
        ajustes = override_settings(BACKUPS_DIR=self.carpeta)
        ajustes.enable()
        self.addCleanup(ajustes.disable)
        self.admin = self.crear_empleado("jefa", "20111222", admin=True)
        self.client.force_login(self.admin.usuario)

    def archivo(self, momento):
        ruta = self.carpeta / momento.strftime(services.FORMATO_NOMBRE)
        ruta.write_bytes(b"copia")
        return ruta

    def acciones(self, accion):
        return list(
            RegistroCambio.objects.filter(accion=accion).values_list("usuario_nombre", flat=True)
        )

    def test_generar_y_descargar_el_ultimo(self):
        self.archivo(datetime(2020, 1, 1, 10))
        self.client.post(reverse("respaldos:generar"))
        nueva = services.ultima()
        self.assertGreater(nueva.tamanio, 1000)

        respuesta = self.client.post(reverse("respaldos:descargar"))
        self.assertIn(nueva.nombre, respuesta["Content-Disposition"])
        self.assertTrue(b"".join(respuesta.streaming_content).startswith(b"PGDMP"))
        self.assertEqual(self.acciones(RegistroCambio.Accion.BACKUP_CREADO), ["jefa"])
        self.assertEqual(self.acciones(RegistroCambio.Accion.BACKUP_DESCARGADO), ["jefa"])
        self.assertFalse(services.conviene_descargar())

    def test_solo_el_administrador(self):
        self.archivo(datetime(2020, 1, 1, 10))
        ana = self.crear_empleado("ana", "30111222")
        self.client.force_login(ana.usuario)
        for nombre in ("respaldos:generar", "respaldos:descargar"):
            self.assertEqual(self.client.post(reverse(nombre)).status_code, 403)
        self.assertEqual(self.client.get(reverse("respaldos:lista")).status_code, 403)

    def test_la_descarga_requiere_post(self):
        self.assertEqual(self.client.get(reverse("respaldos:descargar")).status_code, 405)

    def test_sin_copias_avisa(self):
        respuesta = self.client.post(reverse("respaldos:descargar"), follow=True)
        self.assertContains(respuesta, "Todavía no hay ningún backup")

    def test_un_fallo_no_deja_archivos_y_se_informa(self):
        base_rota = patch.dict(connection.settings_dict, {"NAME": "base_inexistente"})
        with base_rota, self.assertRaises(services.RespaldoError):
            services.crear()
        self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_automatico_solo_cuando_pasaron_24_horas(self):
        comando = Command(stdout=StringIO(), stderr=StringIO())
        comando.revisar()
        comando.revisar()
        self.assertEqual(len(services.listar()), 1)
        self.assertEqual(self.acciones(RegistroCambio.Accion.BACKUP_CREADO), ["Sistema"])

        services.ultima().ruta.unlink()
        self.archivo(timezone.localtime() - timedelta(hours=25))
        comando.revisar()
        self.assertEqual(len(services.listar()), 2)

    def test_conserva_7_diarios_y_4_semanales(self):
        inicio = datetime(2026, 3, 31, 20)
        for dias in range(60):
            self.archivo(inicio - timedelta(days=dias))
        anterior_del_dia = self.archivo(inicio - timedelta(hours=1))

        services.limpiar()

        fechas = [c.momento.date() for c in services.listar()]
        self.assertEqual(len(fechas), 11)
        self.assertEqual(
            fechas[:7], [(inicio - timedelta(days=d)).date() for d in range(7)]
        )
        self.assertEqual(len({f.isocalendar()[:2] for f in fechas[7:]}), 4)
        self.assertFalse(anterior_del_dia.exists())
