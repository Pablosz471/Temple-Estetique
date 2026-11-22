from django.urls import path
from . import views

app_name = "operaciones"
urlpatterns = [
    path("servicios/", views.ServicioListView.as_view(), name="servicios"),
    path("servicios/nuevo/", views.ServicioCreateView.as_view(), name="servicio_crear"),
    path("servicios/<int:pk>/editar/", views.ServicioUpdateView.as_view(), name="servicio_editar"),
    path("servicios/<int:pk>/eliminar/", views.ServicioEstadoView.as_view(), name="servicio_eliminar"),
    path("realizados/", views.RealizadoListView.as_view(), name="realizados"),
    path("realizados/nuevo/", views.RealizadoCreateView.as_view(), name="realizado_crear"),
    path("realizados/<int:pk>/editar/", views.RealizadoUpdateView.as_view(), name="realizado_editar"),
    path("realizados/<int:pk>/eliminar/", views.RealizadoDeleteView.as_view(), name="realizado_eliminar"),
]
