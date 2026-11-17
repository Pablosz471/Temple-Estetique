from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import RegistroAsistenciaForm
from .models import RegistroAsistencia


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self): return self.request.user.is_superuser


class AsistenciaListView(AdminMixin, ListView):
    model = RegistroAsistencia; template_name = "componentes/crud_lista.html"; paginate_by = 20
    titulo = "Asistencias"; descripcion = "Registrá y consultá los horarios del equipo."
    columnas = ("Empleado", "Ingreso", "Salida", "Comisión diaria", "Detalle")
    crear_url = reverse_lazy("asistencias:crear"); lista_url = reverse_lazy("asistencias:lista")

    def get_queryset(self):
        qs = super().get_queryset().select_related("empleado")
        termino = self.request.GET.get("q", "").strip()[:100]
        if termino: qs = qs.filter(Q(empleado__nombre__icontains=termino) | Q(empleado__apellido__icontains=termino))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(titulo=self.titulo, descripcion=self.descripcion, columnas=self.columnas,crear_url=self.crear_url, lista_url=self.lista_url)
        ctx["filas"] = [{"valores": (str(o.empleado), o.fecha_hora_ingreso.strftime("%d/%m/%Y %H:%M"),
            o.fecha_hora_salida.strftime("%d/%m/%Y %H:%M") if o.fecha_hora_salida else "En curso",
            f"$ {o.comision_diaria}", o.detalle or "—"),
            "editar_url": reverse_lazy("asistencias:editar", args=[o.pk]),
            "eliminar_url": reverse_lazy("asistencias:eliminar", args=[o.pk])} for o in ctx["object_list"]]
        return ctx


class GuardarMixin:
    def form_valid(self, form): messages.success(self.request, "Cambios guardados correctamente."); return super().form_valid(form)

class AsistenciaCreateView(AdminMixin, GuardarMixin, CreateView):
    model = RegistroAsistencia; form_class = RegistroAsistenciaForm; template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("asistencias:lista"); titulo = "Registrar asistencia"
class AsistenciaUpdateView(AdminMixin, GuardarMixin, UpdateView):
    model = RegistroAsistencia; form_class = RegistroAsistenciaForm; template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("asistencias:lista"); titulo = "Editar asistencia"

class AsistenciaDeleteView(AdminMixin, DeleteView):
    model = RegistroAsistencia; template_name = "componentes/crud_confirmar.html"
    success_url = reverse_lazy("asistencias:lista"); titulo = "Eliminar asistencia"
    def form_valid(self, form):
        try: response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar este registro porque tiene datos relacionados.")
            return redirect(self.success_url)
        messages.success(self.request, "Registro eliminado."); return response

for _view in (AsistenciaCreateView, AsistenciaUpdateView):
    _view.extra_context = {"titulo": _view.titulo, "lista_url": _view.success_url}
AsistenciaDeleteView.extra_context = {"titulo": AsistenciaDeleteView.titulo, "lista_url": AsistenciaDeleteView.success_url}
