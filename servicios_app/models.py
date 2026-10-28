from django.db import models

class Servicio(models.Model):
nombre_servicio = models.CharField(max_length=50)
descripcion = models.CharField(max_length=100)

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

servicio = models.ForeignKey(
    Servicio,
    on_delete=models.PROTECT,
    related_name="realizaciones",
)

fecha = models.DateField()
monto_servicio = models.DecimalField(max_digits=10, decimal_places=2)
porcentaje_empleado = models.DecimalField(max_digits=5, decimal_places=2)
observacion = models.CharField(max_length=100, blank=True)

class Meta:
    db_table = "servicios_realizados"
    ordering = ["-fecha"]
    verbose_name = "servicio realizado"
    verbose_name_plural = "servicios realizados"

def __str__(self):
    return f"{self.servicio} - {self.empleado} - {self.fecha}"
