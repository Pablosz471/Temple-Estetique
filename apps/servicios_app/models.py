from django.db import models

class Servicio(models.Model):
    nombre_servicio = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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

    fecha = models.DateField()
    monto_servicio = models.DecimalField(max_digits=10, decimal_places=2)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "servicios_realizados"
        ordering = ["-fecha"]
        verbose_name = "servicio realizado"
        verbose_name_plural = "servicios realizados"

    def __str__(self):
        empleado = (
            self.Registro_asistencia.empleado
            if self.Registro_asistencia_id
            else self.empleado
        )
        return f"{self.servicio} - {empleado} - {self.fecha}"
