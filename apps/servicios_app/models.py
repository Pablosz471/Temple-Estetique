from django.utils import timezone
from django.db import models, transaction


def _periodo(empleado_id, fecha_hora):
    """(empleado, año, mes) de un servicio, en hora de Argentina."""
    local = timezone.localtime(fecha_hora)
    return (empleado_id, local.year, local.month)


class Servicio(models.Model):
    nombre_servicio = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    class Meta:
        db_table = "servicios"
        ordering = ["nombre_servicio"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.nombre_servicio


class ServicioRealizado(models.Model):
    empleado = models.ForeignKey(
        "empleados_app.Empleado",
        on_delete=models.PROTECT,
        related_name="servicios_realizados",
    )

    Registro_asistencia = models.ForeignKey(
        "asistencias_app.RegistroAsistencia",
        on_delete=models.PROTECT,
        related_name="servicios_realizados",
        null=True,
        blank=True,
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name="realizaciones",
    )
    fecha_hora = models.DateTimeField()
    monto_servicio = models.DecimalField(max_digits=10, decimal_places=2)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "servicios_realizados"
        ordering = ["-fecha_hora", "-pk"]
        verbose_name = "servicio realizado"
        verbose_name_plural = "servicios realizados"

    def __str__(self):
        empleado = (
            self.Registro_asistencia.empleado
            if self.Registro_asistencia_id
            else self.empleado
        )
        return f"{self.servicio} - {empleado} - {timezone.localtime(self.fecha_hora):%d/%m/%Y %H:%M}"

    def save(self, *args, **kwargs):
        anterior = None
        if self.pk:
            anterior = (
                ServicioRealizado.objects.filter(pk=self.pk)
                .values("Registro_asistencia_id", "empleado_id", "fecha_hora")
                .first()
            )
        with transaction.atomic():
            super().save(*args, **kwargs)
            asistencias = [self.Registro_asistencia_id]
            periodos = [_periodo(self.empleado_id, self.fecha_hora)]
            if anterior:
                asistencias.append(anterior["Registro_asistencia_id"])
                periodos.append(_periodo(anterior["empleado_id"], anterior["fecha_hora"]))
            self._actualizar_comisiones(*asistencias)
            self._actualizar_meses(*periodos)

    def delete(self, *args, **kwargs):
        asistencia_id = self.Registro_asistencia_id
        periodo = _periodo(self.empleado_id, self.fecha_hora)
        with transaction.atomic():
            resultado = super().delete(*args, **kwargs)
            self._actualizar_comisiones(asistencia_id)
            self._actualizar_meses(periodo)
        return resultado

    @staticmethod
    def _actualizar_comisiones(*asistencia_ids):
        from apps.asistencias_app.models import RegistroAsistencia

        ids = [i for i in asistencia_ids if i]
        for asistencia in RegistroAsistencia.objects.filter(pk__in=ids):
            asistencia.actualizar_comision()

    @staticmethod
    def _actualizar_meses(*periodos):
        from apps.liquidaciones_app.models import RegistroMensual

        for empleado_id, anio, mes in set(periodos):
            RegistroMensual.actualizar(empleado_id, anio, mes)

