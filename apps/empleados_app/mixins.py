from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class EmpleadoSoloLecturaMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Pantallas de consulta para usuarios con ficha de empleado que no son administradores."""

    http_method_names = ["get", "head", "options"]

    def test_func(self):
        usuario = self.request.user
        return not usuario.is_superuser and getattr(usuario, "empleado", None) is not None
