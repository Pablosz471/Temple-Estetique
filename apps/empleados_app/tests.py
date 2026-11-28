from django.urls import reverse
from apps.auditoria_app.models import RegistroCambio
from apps.pruebas import CLAVE, PruebaBase
from cuentas.models import Usuario
from .models import Empleado, Rol


class EmpleadosTests(PruebaBase):
    def setUp(self):
        self.admin = self.crear_empleado("jefa", "20111222", admin=True)
        self.client.force_login(self.admin.usuario)

    def datos_alta(self, rol):
        return {
            "username": "nueva", "nombre": "Nueva", "apellido": "Persona",
            "dni": "33111222", "telefono": "3871234567", "email": "nueva@example.test",
            "rol": Rol.objects.get(nombre_rol=rol).pk, "direccion": "",
            "password1": CLAVE, "password2": CLAVE,
        }

    def test_alta_de_empleado_crea_su_usuario(self):
        respuesta = self.client.post(reverse("empleados:empleado_crear"), self.datos_alta(Rol.EMPLEADO))
        self.assertRedirects(respuesta, reverse("empleados:empleados"))
        usuario = Empleado.objects.get(dni="33111222").usuario
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_superuser)
        self.assertTrue(usuario.check_password(CLAVE))

    def test_un_administrador_no_puede_crear_administradores(self):
        respuesta = self.client.post(
            reverse("empleados:empleado_crear"), self.datos_alta(Rol.ADMINISTRADOR)
        )
        self.assertIn("rol", respuesta.context["form"].errors)
        self.assertFalse(Empleado.objects.filter(dni="33111222").exists())

    def test_inhabilitar_quita_el_acceso_y_habilitar_lo_devuelve(self):
        ana = self.crear_empleado("ana", "30111222")
        url = reverse("empleados:empleado_estado", args=[ana.pk])
        for esperado in (False, True):
            self.client.post(url)
            ana.refresh_from_db()
            ana.usuario.refresh_from_db()
            self.assertEqual(ana.activo, esperado)
            self.assertEqual(ana.usuario.is_active, esperado)

    def test_no_puede_inhabilitar_su_propio_perfil(self):
        self.client.post(reverse("empleados:empleado_estado", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_la_lista_muestra_columnas_y_acciones(self):
        self.crear_empleado("ana", "30111222")
        respuesta = self.client.get(reverse("empleados:empleados"))
        fila = respuesta.context["filas"][0]
        self.assertEqual(len(fila["valores"]), len(respuesta.context["columnas"]))
        self.assertContains(respuesta, "Nuevo registro")
        self.assertContains(respuesta, "Editar")
        self.assertContains(respuesta, "Inhabilitar")


class RestablecerPasswordTests(PruebaBase):
    NUEVA = "Otra-clave-segura-678"

    def setUp(self):
        self.admin = self.crear_empleado("jefa", "20111222", admin=True)
        self.ana = self.crear_empleado("ana", "30111222")
        self.client.force_login(self.admin.usuario)
        self.url = reverse("empleados:restablecer_password", args=[self.ana.pk])

    def enviar(self, clave1, clave2=None, url=None):
        return self.client.post(
            url or self.url,
            {"password1": clave1, "password2": clave1 if clave2 is None else clave2},
            follow=True,
        )

    def test_el_boton_esta_en_editar_empleado(self):
        respuesta = self.client.get(reverse("empleados:empleado_editar", args=[self.ana.pk]))
        self.assertContains(respuesta, self.url)
        self.assertContains(self.client.get(self.url), "¿Está seguro que desea restablecer")

    def test_restablece_y_queda_en_el_historial(self):
        respuesta = self.enviar(self.NUEVA)
        self.assertContains(respuesta, "restablecida")
        self.ana.usuario.refresh_from_db()
        self.assertTrue(self.ana.usuario.check_password(self.NUEVA))
        registro = RegistroCambio.objects.get(detalle="Contraseña restablecida.")
        self.assertEqual(registro.usuario_nombre, "jefa")

    def test_mismas_validaciones_que_en_el_alta(self):
        for clave1, clave2 in (
            ("corta1", "corta1"),
            ("1234567890123", "1234567890123"),
            ("password123", "password123"),
            ("ana@example.test", "ana@example.test"),
            (self.NUEVA, "distinta-clave-999"),
            ("", ""),
        ):
            with self.subTest(clave=clave1):
                respuesta = self.enviar(clave1, clave2)
                self.assertTrue(respuesta.context["form"].errors)
        self.ana.usuario.refresh_from_db()
        self.assertTrue(self.ana.usuario.check_password(CLAVE))

    def test_solo_el_administrador(self):
        self.client.force_login(self.ana.usuario)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.enviar(self.NUEVA).status_code, 403)

    def test_restablecer_la_propia_no_cierra_la_sesion(self):
        jefe = self.crear_empleado("jefe", "20999888", admin=True)
        jefe.usuario.is_superuser = True
        jefe.usuario.save()
        self.client.force_login(jefe.usuario)
        url = reverse("empleados:restablecer_password", args=[jefe.pk])
        respuesta = self.enviar(self.NUEVA, url=url)
        self.assertTrue(respuesta.context["user"].is_authenticated)


class NivelesDeAccesoTests(PruebaBase):
    def setUp(self):
        self.root = Usuario.objects.create_superuser("root", "root@example.test", CLAVE)
        self.jefa = self.crear_empleado("jefa", "20111222", admin=True)
        self.otro = self.crear_empleado("otro", "20333444", admin=True)
        self.ana = self.crear_empleado("ana", "30111222")

    def datos(self, rol, **cambios):
        return {
            "username": "nueva", "nombre": "Nueva", "apellido": "Persona",
            "dni": "33111222", "telefono": "3871234567", "email": "nueva@example.test",
            "rol": Rol.objects.get(nombre_rol=rol).pk, "direccion": "",
            "password1": CLAVE, "password2": CLAVE, **cambios,
        }

    def urls_de(self, empleado):
        return [
            reverse(f"empleados:{nombre}", args=[empleado.pk])
            for nombre in ("empleado_editar", "empleado_estado", "restablecer_password")
        ]

    def test_el_superusuario_crea_administradores_sin_permisos_de_django(self):
        self.client.force_login(self.root)
        respuesta = self.client.post(
            reverse("empleados:empleado_crear"), self.datos(Rol.ADMINISTRADOR)
        )
        self.assertRedirects(respuesta, reverse("empleados:empleados"))
        usuario = Usuario.objects.get(username="nueva")
        self.assertTrue(usuario.es_administrador)
        self.assertFalse(usuario.is_superuser or usuario.is_staff)

    def test_el_superusuario_modifica_administradores(self):
        self.client.force_login(self.root)
        for url in self.urls_de(self.jefa):
            self.assertEqual(self.client.get(url).status_code, 200)
        datos = self.datos(Rol.EMPLEADO, dni=self.jefa.dni, email="jefa@example.test")
        self.client.post(self.urls_de(self.jefa)[0], datos)
        self.assertFalse(Usuario.objects.get(username="jefa").es_administrador)

    def test_un_administrador_no_modifica_administradores_ni_a_si_mismo(self):
        self.client.force_login(self.jefa.usuario)
        for empleado in (self.jefa, self.otro):
            for url in self.urls_de(empleado):
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 403)
                    self.assertEqual(self.client.post(url).status_code, 403)
            empleado.refresh_from_db()
            self.assertTrue(empleado.activo)

    def test_un_administrador_no_asciende_a_un_empleado(self):
        self.client.force_login(self.jefa.usuario)
        datos = self.datos(Rol.ADMINISTRADOR, dni=self.ana.dni, email="ana@example.test")
        respuesta = self.client.post(self.urls_de(self.ana)[0], datos)
        self.assertIn("rol", respuesta.context["form"].errors)
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.rol.es_administrador)

    def test_la_lista_solo_ofrece_acciones_permitidas(self):
        self.client.force_login(self.jefa.usuario)
        respuesta = self.client.get(reverse("empleados:empleados"))
        self.assertContains(respuesta, self.urls_de(self.ana)[0])
        self.assertNotContains(respuesta, self.urls_de(self.otro)[0])
        self.assertContains(respuesta, "Solo superusuario")

    def test_solo_el_superusuario_entra_a_admin(self):
        for usuario, estado in ((self.root, 200), (self.jefa.usuario, 302), (self.ana.usuario, 302)):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get("/admin/").status_code, estado)

    def test_el_superusuario_crea_administradores_desde_admin(self):
        self.client.force_login(self.root)
        respuesta = self.client.post(
            reverse("admin:empleados_app_empleado_add"), self.datos(Rol.ADMINISTRADOR)
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Usuario.objects.get(username="nueva").es_administrador)
