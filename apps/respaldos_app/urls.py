from django.urls import path
from . import views

app_name = "respaldos"
urlpatterns = [
    path("", views.RespaldosView.as_view(), name="lista"),
    path("generar/", views.GenerarRespaldoView.as_view(), name="generar"),
    path("descargar/", views.DescargarRespaldoView.as_view(), name="descargar"),
]
