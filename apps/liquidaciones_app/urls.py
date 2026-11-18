from django.urls import path
from . import views

app_name = "liquidaciones"
urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/servicios/", views.servicios_del_mes, name="servicios"),
]
