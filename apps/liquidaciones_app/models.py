from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils import timezone

MESES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)


class RegistroMensual(models.Model):
    empleado = models.ForeignKey(
        "empleados_app.Empleado",
        on_delete=models.PROTECT,
        related_name="registros_mensuales",
    )

    mes = models.PositiveSmallIntegerField()
    anio = models.PositiveSmallIntegerField()
    total_generado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_comisiones = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "registros_mensuales"
        ordering = ["-anio", "-mes"]
        constraints = [
            models.UniqueConstraint(
                fields=["empleado", "mes", "anio"],
                name="registro_mensual_empleado_mes_anio_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(mes__gte=1, mes__lte=12),
                name="registro_mensual_mes_valido",
            ),
        ]
        verbose_name = "registro mensual"
        verbose_name_plural = "registros mensuales"

    def __str__(self):
        return f"{self.empleado} - {self.periodo}"

    @classmethod
    def actualizar(cls, empleado_id, anio, mes):
        """Recalcula el registro del mes desde los servicios realizados (lo crea si no existe)."""
        from apps.asistencias_app.models import RegistroAsistencia
        from apps.servicios_app.models import ServicioRealizado

        total = ServicioRealizado.objects.filter(
            empleado_id=empleado_id, fecha_hora__year=anio, fecha_hora__month=mes
        ).aggregate(total=Sum("monto_servicio"))["total"] or Decimal("0")
        comision = (total * RegistroAsistencia.PORCENTAJE_COMISION).quantize(Decimal("0.01"))
        registro, _ = cls.objects.update_or_create(
            empleado_id=empleado_id,
            anio=anio,
            mes=mes,
            defaults={"total_generado": total, "total_comisiones": comision},
        )
        return registro

    @property
    def periodo(self):
        return f"{MESES[self.mes - 1]} {self.anio}"

    @property
    def clave(self):
        return f"{self.anio}-{self.mes:02d}"

    @property
    def es_mes_actual(self):
        hoy = timezone.localdate()
        return (self.anio, self.mes) == (hoy.year, hoy.month)

    def servicios(self):
        from apps.servicios_app.models import ServicioRealizado

        return ServicioRealizado.objects.filter(
            empleado_id=self.empleado_id,
            fecha_hora__year=self.anio,
            fecha_hora__month=self.mes,
        ).select_related("servicio")
