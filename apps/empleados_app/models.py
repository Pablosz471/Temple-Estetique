from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        db_table = "roles"
        ordering = ["nombre_rol"]
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre_rol


class Empleado(models.Model):
    Estado_choices = [
        ("Activo", "Activo"),
        ("Inactivo", "Inactivo"),
    ]
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="empleado",
    )

    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name="empleados",
    )

    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\d{7,10}$",
                message="El DNI debe contener entre 7 y 10 dígitos.",
            )
        ],
    )

    telefono = models.CharField(max_length=50)
    direccion = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=Estado_choices, default="Activo")
    foto_empleado = models.CharField(max_length=100, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)
    class Meta:
        db_table = "empleados"
        ordering = ["apellido", "nombre"]
        verbose_name = "empleado"
        verbose_name_plural = "empleados"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class HistorialAcceso(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_accesos",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    resultado = models.BooleanField()
    email_ingresado = models.CharField(max_length=50)

    class Meta:
        db_table = "historial_accesos"
        ordering = ["-fecha_hora"]
        verbose_name = "historial de acceso"
        verbose_name_plural = "historiales de acceso"

    def __str__(self):
        return f"{self.empleado} - {self.accion} - {self.fecha_hora}"
