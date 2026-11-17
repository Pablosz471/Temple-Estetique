from django.urls import path
from . import views

app_name = "liquidaciones"
urlpatterns = [
    path("", views.RegistroMensualListView.as_view(), name="lista"),
    path("nuevo/", views.RegistroMensualCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.RegistroMensualUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.RegistroMensualDeleteView.as_view(), name="eliminar"),
]
