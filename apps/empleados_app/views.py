from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.shortcuts import redirect
from apps.mixins import AdminMixin, GuardarMixin, TablaAdminMixin
from .forms import EmpleadoCrearForm, EmpleadoEditarForm
from .models import Empleado, Rol


class EmpleadoListView(TablaAdminMixin):
    model = Empleado
    titulo = "Empleados"
    descripcion = "Administrá los perfiles, roles y estado del equipo."
    columnas = ("Empleado", "Usuario", "DNI", "Rol", "Estado")
    busqueda = ("nombre", "apellido", "dni", "usuario__username", "rol__nombre_rol")
    ordenes = (
        ("nombre", "Nombre (A-Z)", ("apellido", "nombre")),
        ("-nombre", "Nombre (Z-A)", ("-apellido", "-nombre")),
    )
    filtros = (
        {
            "param": "rol", "etiqueta": "Rol", "campo": "rol",
            "opciones": lambda: [(str(r.pk), r.nombre_rol, r.pk) for r in Rol.objects.all()],
        },
        {
            "param": "estado", "etiqueta": "Estado", "campo": "activo",
            "opciones": [("activo", "Activo", True), ("inactivo", "Inactivo", False)],
        },
    )

    crear_url = reverse_lazy("empleados:empleado_crear")
    lista_url = reverse_lazy("empleados:empleados")

    def get_queryset(self):
        return super().get_queryset().select_related("rol", "usuario")

    def valores(self, obj):
        return (str(obj), obj.usuario.username, obj.dni, obj.rol.nombre_rol, "Activo" if obj.activo else "Inactivo")


    def editar_url(self, obj): return reverse_lazy("empleados:empleado_editar", args=[obj.pk])
    def eliminar_url(self, obj): return reverse_lazy("empleados:empleado_estado", args=[obj.pk])


class EmpleadoCreateView(AdminMixin, GuardarMixin, CreateView):
    model = Empleado
    form_class = EmpleadoCrearForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("empleados:empleados")
    titulo = "Registrar empleado"
    lista_url = success_url

class EmpleadoUpdateView(AdminMixin, GuardarMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoEditarForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("empleados:empleados")
    titulo = "Editar empleado"
    lista_url = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario_actual"] = self.request.user

        return kwargs

class EmpleadoEstadoView(AdminMixin, DetailView):
    model = Empleado
    template_name = "componentes/crud_estado.html"

    def post(self, request, *args, **kwargs):
        empleado = self.get_object()
        if empleado.usuario_id == request.user.pk and empleado.activo:
            messages.error(request, "No podés inhabilitar tu propio perfil.")
            return redirect("empleados:empleados")

        empleado.activo = not empleado.activo
        empleado.save(update_fields=["activo"])
        messages.success(request, f"Empleado {'habilitado' if empleado.activo else 'inhabilitado'}.")
        return redirect("empleados:empleados")

    

for _view in (EmpleadoCreateView, EmpleadoUpdateView):
    _view.extra_context = {"titulo": _view.titulo, "lista_url": _view.lista_url}

EmpleadoEstadoView.extra_context = {
    "lista_url": reverse_lazy("empleados:empleados"),
    "entidad":"empleado",
    "consecuencia_baja": "No podrá ingresar al sistema ni se lo podrá elegir en nuevos registros, pero se conserva todo su historial.",
    "consecuencia_alta": "Podrá volver a ingresar al sistema.",
}