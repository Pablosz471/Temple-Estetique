from decimal import Decimal
from django.db import models
from django.db.models import Case, F, Sum, When, Window
from django.db.models.functions import RowNumber, TruncMonth
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
            activo=True, empleado_id=empleado_id, fecha_hora__year=anio, fecha_hora__month=mes
        ).aggregate(total=Sum("monto_servicio"))["total"] or Decimal("0")
        comision = RegistroAsistencia.comision_de(total)
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

    def servicios(self, incluir_inhabilitados=False):
        from apps.servicios_app.models import ServicioRealizado

        servicios = ServicioRealizado.objects.filter(
            empleado_id=self.empleado_id,
            fecha_hora__year=self.anio,
            fecha_hora__month=self.mes,
        ).select_related("servicio")
        return servicios if incluir_inhabilitados else servicios.filter(activo=True)

    @staticmethod
    def cargar_resumenes(empleado, registros, cantidad_ultimos=5, incluir_inhabilitados=False):
        """Agrega a cada registro `ultimos` y `cantidad` con una sola consulta.

        `cantidad` cuenta solo los habilitados, aunque `ultimos` incluya los demás.
        """
        from apps.servicios_app.models import ServicioRealizado

        servicios = ServicioRealizado.objects.filter(empleado=empleado)
        if not incluir_inhabilitados:
            servicios = servicios.filter(activo=True)
        if len(registros) == 1:
            servicios = servicios.filter(
                fecha_hora__year=registros[0].anio, fecha_hora__month=registros[0].mes
            )
        mes = TruncMonth("fecha_hora")
        servicios = (
            servicios.annotate(
                posicion=Window(
                    RowNumber(),
                    partition_by=mes,
                    order_by=[F("fecha_hora").desc(), F("pk").desc()],
                ),
                cantidad_del_mes=Window(
                    Sum(Case(When(activo=True, then=1), default=0)), partition_by=mes
                ),
            )
            .filter(posicion__lte=cantidad_ultimos)
            .select_related("servicio")
            .order_by("-fecha_hora", "-pk")
        )

        por_mes = {}
        for servicio in servicios:
            clave = timezone.localtime(servicio.fecha_hora).strftime("%Y-%m")
            por_mes.setdefault(clave, []).append(servicio)

        for registro in registros:
            registro.ultimos = por_mes.get(registro.clave, [])
            registro.cantidad = registro.ultimos[0].cantidad_del_mes if registro.ultimos else 0


