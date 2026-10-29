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
    
class Aguinaldo(models.Model):
    empleado = models.ForeignKey(
        "empleados_app.Empleado",
        on_delete=models.PROTECT,
        related_name="aguinaldos",
    )

    semestre = models.PositiveSmallIntegerField()
    anio = models.PositiveSmallIntegerField()

    mejor_sueldo_semestre = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    monto_aguinaldo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        db_table = "aguinaldos"
        ordering = ["-anio", "-semestre"]
        constraints = [
            models.UniqueConstraint(
                fields=["empleado", "semestre", "anio"],
                name="aguinaldo_empleado_semestre_anio_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(semestre__in=[1, 2]),
                name="aguinaldo_semestre_valido",
            ),
        ]
        verbose_name = "aguinaldo"
        verbose_name_plural = "aguinaldos"

    def __str__(self):
        return (
            f"Aguinaldo de {self.empleado} - "
            f"Semestre {self.semestre}/{self.anio}"
        )   