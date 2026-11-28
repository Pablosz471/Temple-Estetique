from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "cuentas"
urlpatterns = [
    path("ingresar/", views.AccesoView.as_view(), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
    path("cambiar-contrasena/", views.CambiarPasswordView.as_view(), name="cambiar_password"),
]
