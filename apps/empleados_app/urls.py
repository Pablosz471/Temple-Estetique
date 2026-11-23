from django.urls import path
from . import views

app_name = "empleados"
urlpatterns = [
    path("", views.EmpleadoListView.as_view(), name="empleados"),
    path("nuevo/", views.EmpleadoCreateView.as_view(), name="empleado_crear"),
    path("<int:pk>/editar/", views.EmpleadoUpdateView.as_view(), name="empleado_editar"),
    path("<int:pk>/estado/", views.EmpleadoEstadoView.as_view(), name="empleado_estado"),
]

