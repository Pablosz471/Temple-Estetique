from decimal import Decimal
from django.db import migrations
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear

PORCENTAJE = Decimal("0.40")


def recalcular(apps, schema_editor):
    """Reemplaza los registros cargados a mano por los totales reales de los servicios."""
    RegistroMensual = apps.get_model("liquidaciones_app", "RegistroMensual")
    ServicioRealizado = apps.get_model("servicios_app", "ServicioRealizado")
    RegistroMensual.objects.all().delete()
    filas = (
        ServicioRealizado.objects.annotate(
            anio=ExtractYear("fecha_hora"), mes=ExtractMonth("fecha_hora")
        )
        .values("empleado_id", "anio", "mes")
        .annotate(total=Sum("monto_servicio"))
        .order_by()
    )
    RegistroMensual.objects.bulk_create(
        [
            RegistroMensual(
                empleado_id=fila["empleado_id"],
                anio=fila["anio"],
                mes=fila["mes"],
                total_generado=fila["total"],
                total_comisiones=(fila["total"] * PORCENTAJE).quantize(Decimal("0.01")),
            )
            for fila in filas
        ]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("liquidaciones_app", "0004_alter_registromensual_total_comisiones"),
        ("servicios_app", "0005_alter_serviciorealizado_options_and_more"),
    ]

    operations = [
        migrations.RunPython(recalcular, migrations.RunPython.noop),
    ]
