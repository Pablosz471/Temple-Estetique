import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor

from apps.respaldos_app import services

REVISAR_CADA = 15 * 60
ESPERA_DE_MIGRACIONES = 30


class Command(BaseCommand):
    help = "Revisa periódicamente y crea un backup si el último tiene más de 24 horas."

    def handle(self, *args, **options):
        while True:
            close_old_connections()  # descarta conexiones caídas durante la espera
            time.sleep(self.revisar())

    def revisar(self):
        """Hace una revisión y devuelve los segundos a esperar hasta la siguiente."""
        try:
            executor = MigrationExecutor(connection)
            if executor.migration_plan(executor.loader.graph.leaf_nodes()):
                self.stdout.write("Esperando que se apliquen las migraciones.")
                return ESPERA_DE_MIGRACIONES
            if services.hace_falta_una_nueva():
                copia = services.crear()
                self.stdout.write(f"Backup creado: {copia.nombre}")
        except Exception as error:  # el servicio sigue y vuelve a intentar
            self.stderr.write(f"No se pudo hacer el backup automático: {error}")
        return REVISAR_CADA
