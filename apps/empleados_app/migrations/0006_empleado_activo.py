from django.db import migrations, models


def estado_a_activo(apps, schema_editor):
    Empleado = apps.get_model("empleados_app", "Empleado")
    Empleado.objects.filter(estado="Inactivo").update(activo=False)


def activo_a_estado(apps, schema_editor):
    Empleado = apps.get_model("empleados_app", "Empleado")
    Empleado.objects.filter(activo=False).update(estado="Inactivo")


class Migration(migrations.Migration):

    dependencies = [
        ("empleados_app", "0005_alter_empleado_dni"),
    ]

    operations = [
        migrations.AddField(
            model_name="empleado",
            name="activo",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(estado_a_activo, activo_a_estado),
        migrations.RemoveField(
            model_name="empleado",
            name="estado",
        ),
    ]
