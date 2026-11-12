from django.db import models


class RegistroMensual(models.Model):
    empleado = models.ForeignKey(
        "empleados_app.Empleado",
        on_delete=models.PROTECT,
        related_name="registros_mensuales",
    )

    mes = models.PositiveSmallIntegerField()
    anio = models.PositiveSmallIntegerField()
    total_generado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total_porcentaje = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

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
        return f"{self.empleado} - {self.mes}/{self.anio}"
    