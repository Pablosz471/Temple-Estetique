from decimal import Decimal
from django.db import models
from django.db.models import F, Q, Sum


class RegistroAsistencia(models.Model):
    PORCENTAJE_COMISION = Decimal("0.40")

    empleado = models.ForeignKey(
        "empleados_app.Empleado",
        on_delete=models.PROTECT,
        related_name="asistencias",
    )

    fecha_hora_ingreso = models.DateTimeField()
    fecha_hora_salida = models.DateTimeField(null=True, blank=True)
    comision_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    detalle = models.CharField(max_length=150, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "registros_asistencias"
        ordering = ["-fecha_hora_ingreso"]
        verbose_name = "registro de asistencia"
        verbose_name_plural = "registros de asistencias"
        constraints = [
            models.UniqueConstraint(
                fields=["empleado"],
                condition=Q(fecha_hora_salida__isnull=True),
                name="asistencia_una_abierta_por_empleado",
            ),
            models.CheckConstraint(
                condition=Q(fecha_hora_salida__isnull=True)
                | Q(fecha_hora_salida__gte=F("fecha_hora_ingreso")),
                name="asistencia_salida_posterior_al_ingreso",
            ),
        ]

    def __str__(self):
        return f"{self.empleado} - {self.fecha_hora_ingreso:%d/%m/%Y}"

    @property
    def abierta(self):
        return self.fecha_hora_salida is None

    def calcular_comision(self):
        total = self.servicios_realizados.filter(activo=True).aggregate(total=Sum("monto_servicio"))["total"]
        return self.comision_de(total)

    @classmethod
    def comision_de(cls, total):
        """Comisión que corresponde a un total generado (None cuenta como cero)."""
        return ((total or Decimal("0")) * cls.PORCENTAJE_COMISION).quantize(Decimal("0.01"))

    def actualizar_comision(self):
        """Solo las asistencias cerradas tienen comisión calculada."""
        if not self.abierta:
            self.comision_diaria = self.calcular_comision()
            self.save(update_fields=["comision_diaria"])
