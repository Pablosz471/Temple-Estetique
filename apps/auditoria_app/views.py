from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.views.generic import ListView
from .models import RegistroCambio


class HistorialListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = RegistroCambio
    template_name = "auditoria/lista.html"
    paginate_by = 30

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        qs = super().get_queryset()
        termino = self.request.GET.get("q", "").strip()[:100]
        if termino:
            qs = qs.filter(
                Q(usuario_nombre__icontains=termino)
                | Q(modelo__icontains=termino)
                | Q(objeto__icontains=termino)
                | Q(detalle__icontains=termino)
            )
        return qs
