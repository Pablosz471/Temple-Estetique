from django.urls import path
from . import views

app_name = "liquidaciones"
urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/servicios/", views.ServiciosDelMesView.as_view(), name="servicios"),
    path("mis-liquidaciones/", views.MisLiquidacionesView.as_view(), name="mis_liquidaciones"),
    path(
        "mis-liquidaciones/<int:pk>/servicios/",
        views.MisServiciosDelMesView.as_view(),
        name="mis_servicios_del_mes",
    ),
]
