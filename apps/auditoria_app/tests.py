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

    def test_el_filtro_ofrece_inhabilitacion_y_no_eliminacion(self):
        self.client.force_login(self.crear_empleado("jefa", "20111222", admin=True).usuario)
        respuesta = self.client.get(reverse("auditoria:lista"))
        self.assertContains(respuesta, 'value="inhabilitacion"')
        self.assertNotContains(respuesta, 'value="eliminacion"')
