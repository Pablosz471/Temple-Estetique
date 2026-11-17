from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.servicios_app.models import Servicio


class Command(BaseCommand):
    help = (
        "Agrega servicios ficticios sin modificar registros existentes. No crea cuentas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario", required=True, help="Nombre del administrador existente"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            usuario = get_user_model().objects.get(
                username=options["usuario"], is_superuser=True, is_active=True
            )
        except get_user_model().DoesNotExist:
            raise CommandError("Primero creá un administrador con createsuperuser.")
        for nombre, descripcion, precio in [
            ("Limpieza facial", "Servicio de ejemplo para personalizar.", "0.00"),
            ("Manicura", "Servicio de ejemplo para personalizar.", "0.00"),
            ("Masaje relajante", "Servicio de ejemplo para personalizar.", "0.00"),
        ]:
            Servicio.objects.get_or_create(
                nombre_servicio=nombre,
                defaults={"descripcion": descripcion, "precio": precio},
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Servicios de ejemplo disponibles; los registros existentes se conservaron."
            )
        )
