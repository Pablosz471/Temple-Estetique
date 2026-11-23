from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction


class Rol(models.Model):

    ADMINISTRADOR ="Administrador"
    EMPLEADO ="Empleado"

    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100)

    class Meta:
        db_table = "roles"
        ordering = ["nombre_rol"]
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre_rol

    @property
    def es_administrador(self):
        return self.nombre_rol == self.ADMINISTRADOR


class Empleado(models.Model):

    activo = models.BooleanField(default=True)

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
                regex=r"^\d{7,8}$",
                message="El DNI debe contener entre 7 y 8 digitos, solo números.",
            )
        ],
    )

    telefono = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^[0-9]{6,20}$",
                message="Ingresá un teléfono válido: solo se permiten números (entre 6 y 20 dígitos)."            )
        ],
    )
    direccion = models.CharField(max_length=100, blank=True)
    foto_empleado = models.CharField(max_length=100, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)
    class Meta:
        db_table = "empleados"
        ordering = ["apellido", "nombre"]
        verbose_name = "empleado"
        verbose_name_plural = "empleados"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            usuario = self.usuario 
            if usuario.is_active != self.activo:
                usuario.is_active = self.activo
                if self.activo:
                    usuario.estado = usuario.Estado.APROBADO
                usuario.save(update_fields=["is_active", "estado"])


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
        resultado = "correcto" if self.resultado else "fallido"
        return f"{self.email_ingresado} - {resultado} - {self.fecha_hora:%d/%m/%Y %H:%M}"

