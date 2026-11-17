from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from .forms import EmpleadoCrearForm, EmpleadoEditarForm
from .models import Empleado


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class TablaAdminMixin(AdminMixin, ListView):
    template_name = "componentes/crud_lista.html"
    paginate_by = 20
    columnas = ()
    busqueda = ()

    def get_queryset(self):
        qs = super().get_queryset()
        termino = self.request.GET.get("q", "").strip()[:100]
        if termino and self.busqueda:
            filtro = Q()
            for campo in self.busqueda:
                filtro |= Q(**{f"{campo}__icontains": termino})
            qs = qs.filter(filtro)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(titulo=self.titulo, descripcion=self.descripcion, columnas=self.columnas,crear_url=self.crear_url, lista_url=self.lista_url)
        ctx["filas"] = [{"valores": self.valores(obj), "editar_url": self.editar_url(obj),"eliminar_url": self.eliminar_url(obj)} for obj in ctx["object_list"]]
        return ctx


class EmpleadoListView(TablaAdminMixin):
    model = Empleado
    titulo = "Personal"
    descripcion = "Administrá los perfiles, roles y estado del equipo."
    columnas = ("Empleado", "Usuario", "DNI", "Rol")
    busqueda = ("nombre", "apellido", "dni", "usuario__username", "rol__nombre_rol")
    crear_url = reverse_lazy("personal:empleado_crear")
    lista_url = reverse_lazy("personal:empleados")

    def get_queryset(self):
        return super().get_queryset().select_related("rol", "usuario")

    def valores(self, obj):
        return (str(obj), obj.usuario.username, obj.dni, obj.rol.nombre_rol)

    def editar_url(self, obj): return reverse_lazy("personal:empleado_editar", args=[obj.pk])
    def eliminar_url(self, obj): return reverse_lazy("personal:empleado_eliminar", args=[obj.pk])


class GuardarMixin:
    def form_valid(self, form):
        messages.success(self.request, "Cambios guardados correctamente.")
        return super().form_valid(form)


class EmpleadoCreateView(AdminMixin, GuardarMixin, CreateView):
    model = Empleado
    form_class = EmpleadoCrearForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("personal:empleados")
    titulo = "Registrar empleado"
    lista_url = success_url

class EmpleadoUpdateView(AdminMixin, GuardarMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoEditarForm
    template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("personal:empleados")
    titulo = "Editar empleado"
    lista_url = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario_actual"] = self.request.user
        return kwargs

class BajaMixin(AdminMixin, DeleteView):
    template_name = "componentes/crud_confirmar.html"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: hay registros relacionados.")
            return redirect(self.success_url)
        messages.success(self.request, "Registro eliminado.")
        return response

class EmpleadoDeleteView(BajaMixin):
    model = Empleado
    success_url = reverse_lazy("personal:empleados")
    titulo = "Eliminar empleado"

    def form_valid(self, form):
        if self.object.usuario_id == self.request.user.pk:
            messages.error(self.request, "No podés eliminar tu propio perfil.")
            return redirect(self.success_url)
        usuario = self.object.usuario
        respuesta = super().form_valid(form)
        if self.object.pk is None:  # Django lo pone en None cuando el borrado funcionó
            usuario.is_active = False
            usuario.save(update_fields=["is_active"])
        return respuesta

for _view in (EmpleadoCreateView, EmpleadoUpdateView):
    _view.extra_context = {"titulo": _view.titulo, "lista_url": _view.lista_url}
EmpleadoDeleteView.extra_context = {"titulo": EmpleadoDeleteView.titulo, "lista_url": EmpleadoDeleteView.success_url}