from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.shortcuts import redirect
from apps.listados import ListadoMixin
from .forms import EmpleadoCrearForm, EmpleadoEditarForm
from .models import Empleado, Rol


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class TablaAdminMixin(AdminMixin, ListadoMixin, ListView):
    template_name = "componentes/crud_lista.html"
    paginate_by = 20
    columnas = ()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(titulo=self.titulo, descripcion=self.descripcion, columnas=self.columnas, crear_url=self.crear_url, lista_url=self.lista_url)
        ctx["filas"] = [{"valores": self.valores(obj), "editar_url": self.editar_url(obj), "eliminar_url": self.eliminar_url(obj), "baja_texto": self.baja_texto(obj), "inhabilitada": not obj.activo} for obj in ctx["object_list"]]
        return ctx

    def baja_texto(self, obj):
        return "Inhabilitar"


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


    def baja_texto(self, obj):
        return "Inhabilitar" if obj.activo else "Habilitar"

    def editar_url(self, obj): return reverse_lazy("empleados:empleado_editar", args=[obj.pk])
    def eliminar_url(self, obj): return reverse_lazy("empleados:empleado_estado", args=[obj.pk])


class GuardarMixin:
    def form_valid(self, form):
        messages.success(self.request, "Cambios guardados correctamente.")
        return super().form_valid(form)


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