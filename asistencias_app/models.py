from django.db import models

class RegistroAsistencia(models.Model):
empleado = models.ForeignKey(
"empleados_app.Empleado",
on_delete=models.PROTECT,
related_name="asistencias",
)

fecha_hora_ingreso = models.DateTimeField()
fecha_hora_salida = models.DateTimeField(null=True, blank=True)
sueldo_diario = models.DecimalField(max_digits=10, decimal_places=2)
detalle = models.CharField(max_length=100, blank=True)

class Meta:
    db_table = "registros_asistencias"
    ordering = ["-fecha_hora_ingreso"]
    verbose_name = "registro de asistencia"
    verbose_name_plural = "registros de asistencias"

def __str__(self):
    return f"{self.empleado} - {self.fecha_hora_ingreso:%d/%m/%Y}"
