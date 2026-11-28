"""Creación, listado y limpieza de las copias de seguridad de la base de datos."""

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from apps.auditoria_app.contexto import quien
from apps.auditoria_app.models import RegistroCambio

FORMATO_NOMBRE = "backup-%Y-%m-%d_%H%M%S.dump"
PATRON_NOMBRE = re.compile(r"^backup-\d{4}-\d{2}-\d{2}_\d{6}\.dump$")
FRECUENCIA = timedelta(hours=24)
COPIAS_DIARIAS = 7
COPIAS_SEMANALES = 4
DIAS_SIN_DESCARGAR = 7
SEGUNDOS_MAXIMOS = 120


class RespaldoError(Exception):
    """Un error que se le muestra al administrador tal cual."""


@dataclass(frozen=True)
class Copia:
    ruta: Path
    momento: datetime  # hora local del salón

    @property
    def nombre(self):
        return self.ruta.name

    @property
    def tamanio(self):
        return self.ruta.stat().st_size


def _carpeta():
    carpeta = Path(settings.BACKUPS_DIR)
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def listar():
    """Copias disponibles, de la más reciente a la más antigua."""
    copias = [
        Copia(ruta, timezone.make_aware(datetime.strptime(ruta.name, FORMATO_NOMBRE)))
        for ruta in _carpeta().iterdir()
        if PATRON_NOMBRE.match(ruta.name)
    ]
    return sorted(copias, key=lambda c: c.nombre, reverse=True)


def ultima():
    return next(iter(listar()), None)


def hace_falta_una_nueva():
    copia = ultima()
    return copia is None or timezone.now() - copia.momento >= FRECUENCIA


def _ejecutar(comando, entorno):
    try:
        subprocess.run(
            comando, env=entorno, check=True, capture_output=True, timeout=SEGUNDOS_MAXIMOS
        )
    except FileNotFoundError as error:
        raise RespaldoError(
            "Falta la herramienta de backup. Hay que reconstruir la imagen de Docker."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise RespaldoError("El backup tardó demasiado y se canceló.") from error
    except subprocess.CalledProcessError as error:
        detalle = error.stderr.decode(errors="replace").strip()
        raise RespaldoError(f"No se pudo crear el backup: {detalle[-300:]}") from error


def crear():
    """Genera una copia nueva, comprueba que se pueda leer y borra las que sobran."""
    base = connection.settings_dict
    entorno = {**os.environ, "PGPASSWORD": base["PASSWORD"]}
    destino = _carpeta() / timezone.localtime().strftime(FORMATO_NOMBRE)
    # Se escribe en un archivo temporal: una copia a medias nunca figura como disponible.
    descriptor, temporal = tempfile.mkstemp(dir=destino.parent, suffix=".tmp")
    os.close(descriptor)
    try:
        _ejecutar(
            [
                "pg_dump", "--format=custom", "--no-password",
                "--host", base["HOST"], "--port", str(base["PORT"]),
                "--username", base["USER"], "--file", temporal, base["NAME"],
            ],
            entorno,
        )
        _ejecutar(["pg_restore", "--list", temporal], entorno)
        os.replace(temporal, destino)
    finally:
        Path(temporal).unlink(missing_ok=True)
    copia = Copia(destino, timezone.make_aware(datetime.strptime(destino.name, FORMATO_NOMBRE)))
    registrar(RegistroCambio.Accion.BACKUP_CREADO, copia)
    limpiar()
    return copia


def _a_conservar(copias):
    """La última de cada uno de los 7 días más recientes y, antes de eso, 4 semanales."""
    diarias, semanales = {}, {}
    for copia in copias:  # vienen de la más reciente a la más antigua
        dia = copia.momento.date()
        if dia in diarias:
            continue
        if len(diarias) < COPIAS_DIARIAS:
            diarias[dia] = copia
            continue
        semana = dia.isocalendar()[:2]
        if semana not in semanales and len(semanales) < COPIAS_SEMANALES:
            semanales[semana] = copia
    return {*diarias.values(), *semanales.values()}


def limpiar():
    copias = listar()
    conservar = _a_conservar(copias)
    for copia in copias:
        if copia not in conservar:
            copia.ruta.unlink(missing_ok=True)


def registrar(accion, copia):
    usuario, nombre = quien()
    RegistroCambio.objects.create(
        usuario=usuario,
        usuario_nombre=nombre,
        accion=accion,
        modelo="Backup",
        objeto=copia.nombre,
    )


def ultima_descarga():
    return RegistroCambio.objects.filter(accion=RegistroCambio.Accion.BACKUP_DESCARGADO).first()


def conviene_descargar():
    descarga = ultima_descarga()
    return descarga is None or timezone.now() - descarga.fecha_hora >= timedelta(
        days=DIAS_SIN_DESCARGAR
    )
