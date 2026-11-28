"""Piezas comunes a las vistas: control de acceso, tablas y guardado."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from apps.listados import ListadoMixin


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.es_administrador


class EmpleadoSoloLecturaMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Pantallas de consulta para usuarios con ficha de empleado que no son administradores."""

    http_method_names = ["get", "head", "options"]

    def test_func(self):
        usuario = self.request.user
        return not usuario.es_administrador and getattr(usuario, "empleado", None) is not None


class TablaAdminMixin(AdminMixin, ListadoMixin, ListView):
    """Tabla del administrador con las acciones de editar e inhabilitar.

    Cada vista define `valores`, `editar_url` y `eliminar_url`.
    """

    template_name = "componentes/crud_lista.html"
    paginate_by = 20
    columnas = ()
    crear_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            titulo=self.titulo,
            descripcion=self.descripcion,
            columnas=self.columnas,
            crear_url=self.crear_url,
            lista_url=self.lista_url,
        )
        ctx["filas"] = [
            {
                "valores": self.valores(obj),
                "editar_url": self.editar_url(obj),
                "eliminar_url": self.eliminar_url(obj),
                "baja_texto": "Inhabilitar" if obj.activo else "Habilitar",
                "inhabilitada": not obj.activo,
            }
            for obj in ctx["object_list"]
        ]
        return ctx


class GuardarMixin:
    def form_valid(self, form):
        messages.success(self.request, "Cambios guardados correctamente.")
        return super().form_valid(form)
