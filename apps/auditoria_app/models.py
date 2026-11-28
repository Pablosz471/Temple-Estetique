from django.conf import settings
from django.db import models


class RegistroCambio(models.Model):
    class Accion(models.TextChoices):
        CREACION = "creacion", "Alta"
        MODIFICACION = "modificacion", "Modificación"
        INHABILITACION = "inhabilitacion", "Inhabilitación"
        ELIMINACION = "eliminacion", "Eliminación"
        INGRESO = "ingreso", "Ingreso al sistema"
        INGRESO_FALLIDO = "ingreso_fallido", "Intento de ingreso fallido"

    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    usuario_nombre = models.CharField(max_length=150)
    accion = models.CharField(max_length=20, choices=Accion.choices)
    modelo = models.CharField(max_length=60, blank=True)
    objeto = models.CharField(max_length=200, blank=True)
    detalle = models.TextField(blank=True)

    class Meta:
        db_table = "registro_cambios"
        ordering = ["-fecha_hora", "-pk"]
        verbose_name = "registro de cambio"
        verbose_name_plural = "historial de cambios"

    def __str__(self):
        return f"{self.fecha_hora:%d/%m/%Y %H:%M} - {self.usuario_nombre} - {self.get_accion_display()}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("El historial no se puede modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("El historial no se puede borrar.")
