from django.urls import path
from . import views

app_name = "personal"
urlpatterns = [
    path("empleados/", views.EmpleadoListView.as_view(), name="empleados"),
    path("empleados/nuevo/", views.EmpleadoCreateView.as_view(), name="empleado_crear"),
    path("empleados/<int:pk>/editar/", views.EmpleadoUpdateView.as_view(), name="empleado_editar"),
    path("empleados/<int:pk>/eliminar/", views.EmpleadoDeleteView.as_view(), name="empleado_eliminar"),
    path("roles/", views.RolListView.as_view(), name="roles"),
    path("roles/nuevo/", views.RolCreateView.as_view(), name="rol_crear"),
    path("roles/<int:pk>/editar/", views.RolUpdateView.as_view(), name="rol_editar"),
    path("roles/<int:pk>/eliminar/", views.RolDeleteView.as_view(), name="rol_eliminar"),
]
