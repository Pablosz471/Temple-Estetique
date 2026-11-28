from django.urls import reverse
from apps.pruebas import PruebaBase
from apps.servicios_app.models import Servicio
from .models import RegistroCambio


class HistorialTests(PruebaBase):
    def ultima_accion(self):
        return RegistroCambio.objects.order_by("-pk").first().accion

    def test_distingue_alta_modificacion_e_inhabilitacion(self):
        servicio = Servicio.objects.create(nombre_servicio="Corte", descripcion="Prueba", precio=1)
        self.assertEqual(self.ultima_accion(), RegistroCambio.Accion.CREACION)

        servicio.activo = False
        servicio.save(update_fields=["activo"])
        self.assertEqual(self.ultima_accion(), RegistroCambio.Accion.INHABILITACION)

        servicio.activo = True
        servicio.save(update_fields=["activo"])
        self.assertEqual(self.ultima_accion(), RegistroCambio.Accion.MODIFICACION)

    def test_muestra_diez_registros_y_ver_mas_los_extiende(self):
        self.client.force_login(self.crear_empleado("jefa", "20111222", admin=True).usuario)
        for numero in range(25):
            Servicio.objects.create(nombre_servicio=f"Corte {numero}", descripcion="Prueba", precio=1)
        total = RegistroCambio.objects.count()
        url = reverse("auditoria:lista")

        respuesta = self.client.get(url)
        self.assertEqual(len(respuesta.context["page_obj"]), 10)
        self.assertContains(respuesta, 'href="?mostrar=20"')

        self.assertNotContains(respuesta, 'id="ver-menos-registros"')

        respuesta = self.client.get(url, {"mostrar": 20})
        self.assertEqual(len(respuesta.context["page_obj"]), 20)
        self.assertContains(respuesta, 'id="ver-menos-registros"')

        respuesta = self.client.get(url, {"mostrar": total})
        self.assertEqual(len(respuesta.context["page_obj"]), total)
        self.assertNotContains(respuesta, 'id="ver-mas-registros"')

        respuesta = self.client.get(url, {"mostrar": "abc"})
        self.assertEqual(len(respuesta.context["page_obj"]), 10)

    def test_el_filtro_ofrece_inhabilitacion_y_no_eliminacion(self):
        self.client.force_login(self.crear_empleado("jefa", "20111222", admin=True).usuario)
        respuesta = self.client.get(reverse("auditoria:lista"))
        self.assertContains(respuesta, 'value="inhabilitacion"')
        self.assertNotContains(respuesta, 'value="eliminacion"')
