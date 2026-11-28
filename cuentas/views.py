from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from .forms import AccesoForm


class AccesoView(LoginView):
    template_name = "cuentas/login.html"
    authentication_form = AccesoForm
    redirect_authenticated_user = True


class CambiarPasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "cuentas/cambiar_password.html"
    success_url = reverse_lazy("inicio:home")
    success_message = "Tu contraseña se cambió correctamente."
