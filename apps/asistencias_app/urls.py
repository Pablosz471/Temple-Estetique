from django.urls import path
from . import views

app_name = "asistencias"
urlpatterns = [
    path("", views.AsistenciaListView.as_view(), name="lista"),
    path("marcar/", views.marcar, name="marcar"),
    path("<int:pk>/editar/", views.AsistenciaUpdateView.as_view(), name="editar"),
    path("<int:pk>/estado/", views.AsistenciaEstadoView.as_view(), name="estado"),
]
