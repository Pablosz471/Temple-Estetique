from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, View

from apps.auditoria_app.models import RegistroCambio
from apps.mixins import AdminMixin
from . import services


class RespaldosView(AdminMixin, TemplateView):
    template_name = "respaldos/lista.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        copias = services.listar()
        ctx.update(
            copias=copias,
            ultima=copias[0] if copias else None,
            atrasada=services.hace_falta_una_nueva(),
            ultima_descarga=services.ultima_descarga(),
            conviene_descargar=services.conviene_descargar(),
            dias_sin_descargar=services.DIAS_SIN_DESCARGAR,
        )
        return ctx


class GenerarRespaldoView(AdminMixin, View):
    def post(self, request):
        try:
            services.crear()
        except services.RespaldoError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, "Backup generado correctamente.")
        return redirect("respaldos:lista")


class DescargarRespaldoView(AdminMixin, View):
    """Entrega la copia más reciente. Es por POST para que quede protegida con CSRF."""

    def post(self, request):
        copia = services.ultima()
        if copia is None:
            messages.error(request, "Todavía no hay ningún backup para descargar.")
            return redirect("respaldos:lista")
        archivo = copia.ruta.open("rb")
        services.registrar(RegistroCambio.Accion.BACKUP_DESCARGADO, copia)
        return FileResponse(archivo, as_attachment=True, filename=copia.nombre)
