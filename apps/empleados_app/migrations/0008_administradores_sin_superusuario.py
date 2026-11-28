from django.db import migrations


def quitar_permisos_de_django(apps, schema_editor):
    """El rol Administrador deja de dar superusuario y acceso a /admin.

    Las cuentas creadas con createsuperuser no tienen ficha de empleado y no cambian.
    """
    Usuario = apps.get_model("cuentas", "Usuario")
    Usuario.objects.filter(empleado__rol__nombre_rol="Administrador").update(
        is_superuser=False, is_staff=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("cuentas", "0001_initial"),
        ("empleados_app", "0007_delete_historialacceso"),
    ]

    operations = [
        migrations.RunPython(quitar_permisos_de_django, migrations.RunPython.noop),
    ]
