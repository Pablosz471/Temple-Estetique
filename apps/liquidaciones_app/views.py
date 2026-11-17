from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import RegistroMensualForm
from .models import RegistroMensual


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self): return self.request.user.is_superuser


class RegistroMensualListView(AdminMixin, ListView):
    model = RegistroMensual; template_name = "componentes/crud_lista.html"; paginate_by = 20
    titulo = "Liquidaciones mensuales"; descripcion = "Administrá los totales mensuales por integrante del equipo."
    columnas = ("Empleado", "Período", "Total generado", "Total de comisión")
    crear_url = reverse_lazy("liquidaciones:crear"); lista_url = reverse_lazy("liquidaciones:lista")

    def get_queryset(self):
        qs = super().get_queryset().select_related("empleado")
        termino = self.request.GET.get("q", "").strip()[:100]
        if termino: qs = qs.filter(Q(empleado__nombre__icontains=termino) | Q(empleado__apellido__icontains=termino))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(titulo=self.titulo, descripcion=self.descripcion, columnas=self.columnas,
                   crear_url=self.crear_url, lista_url=self.lista_url)
        ctx["filas"] = [{"valores": (str(o.empleado), f"{o.mes:02d}/{o.anio}",
            f"$ {o.total_generado}", f"$ {o.total_comisiones}"),
            "editar_url": reverse_lazy("liquidaciones:editar", args=[o.pk]),
            "eliminar_url": reverse_lazy("liquidaciones:eliminar", args=[o.pk])} for o in ctx["object_list"]]
        return ctx


class GuardarMixin:
    def form_valid(self, form): messages.success(self.request, "Cambios guardados correctamente."); return super().form_valid(form)

class RegistroMensualCreateView(AdminMixin, GuardarMixin, CreateView):
    model = RegistroMensual; form_class = RegistroMensualForm; template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("liquidaciones:lista"); titulo = "Nueva liquidación mensual"
class RegistroMensualUpdateView(AdminMixin, GuardarMixin, UpdateView):
    model = RegistroMensual; form_class = RegistroMensualForm; template_name = "componentes/crud_form.html"
    success_url = reverse_lazy("liquidaciones:lista"); titulo = "Editar liquidación mensual"

class RegistroMensualDeleteView(AdminMixin, DeleteView):
    model = RegistroMensual; template_name = "componentes/crud_confirmar.html"
    success_url = reverse_lazy("liquidaciones:lista"); titulo = "Eliminar liquidación mensual"
    def form_valid(self, form):
        try: response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar este registro porque tiene datos relacionados.")
            return redirect(self.success_url)
        messages.success(self.request, "Registro eliminado."); return response

for _view in (RegistroMensualCreateView, RegistroMensualUpdateView):
    _view.extra_context = {"titulo": _view.titulo, "lista_url": _view.success_url}
RegistroMensualDeleteView.extra_context = {"titulo": RegistroMensualDeleteView.titulo, "lista_url": RegistroMensualDeleteView.success_url}
