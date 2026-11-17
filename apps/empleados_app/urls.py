from django.urls import path
from . import views

app_name = "personal"
urlpatterns = [
    path("empleados/", views.EmpleadoListView.as_view(), name="empleados"),
    path("empleados/nuevo/", views.EmpleadoCreateView.as_view(), name="empleado_crear"),
    path("empleados/<int:pk>/editar/", views.EmpleadoUpdateView.as_view(), name="empleado_editar"),
    path("empleados/<int:pk>/eliminar/", views.EmpleadoDeleteView.as_view(), name="empleado_eliminar"),
]
