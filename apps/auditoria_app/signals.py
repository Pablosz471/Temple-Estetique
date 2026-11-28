from datetime import datetime
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from apps.formatos import fecha_hora
from .contexto import quien
from .models import RegistroCambio

APPS_SEGUIDAS = {
    "cuentas",
    "empleados_app",
    "asistencias_app",
    "servicios_app",
    "liquidaciones_app",
}
MODELOS_EXCLUIDOS = {"RegistroCambio", "RegistroMensual"}
CAMPOS_IGNORADOS = {"password", "last_login", "comision_diaria"}
CAMPOS_DE_ESTADO = ("activo", "is_active")


def _seguido(modelo):
    # Las migraciones usan modelos históricos y pueden correr antes de que exista el historial.
    return (
        modelo.__module__ != "__fake__"
        and modelo._meta.app_label in APPS_SEGUIDAS
        and modelo.__name__ not in MODELOS_EXCLUIDOS
    )


def _etiqueta(campo):
    return str(campo.verbose_name).capitalize()


def _texto(campo, valor):
    if valor is None or valor == "":
        return "—"
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, datetime):
        return fecha_hora(valor)
    if campo.is_relation:
        relacionado = campo.related_model._base_manager.filter(pk=valor).first()
        return str(relacionado) if relacionado else str(valor)
    if campo.choices:
        return str(dict(campo.flatchoices).get(valor, valor))
    return str(valor)


def _campos(instancia, update_fields):
    return [
        campo
        for campo in instancia._meta.concrete_fields
        if campo.name not in CAMPOS_IGNORADOS
        and (
            update_fields is None
            or campo.name in update_fields
            or campo.attname in update_fields
        )
    ]


def _resumen(instancia):
    partes = []
    for campo in _campos(instancia, None):
        if campo.primary_key:
            continue
        valor = getattr(instancia, campo.attname)
        if valor is None or valor == "":
            continue
        partes.append(f"{_etiqueta(campo)}: {_texto(campo, valor)}")
    return "; ".join(partes)


def _diferencias(instancia, previo, update_fields):
    if not previo:
        return []
    cambios = []
    for campo in _campos(instancia, update_fields):
        antes = previo.get(campo.attname)
        ahora = getattr(instancia, campo.attname)
        if antes != ahora:
            cambios.append(
                f"{_etiqueta(campo)}: {_texto(campo, antes)} → {_texto(campo, ahora)}"
            )
    return cambios


def _es_inhabilitacion(instancia, previo, update_fields):
    return any(
        previo.get(campo.attname) is True and getattr(instancia, campo.attname) is False
        for campo in _campos(instancia, update_fields)
        if campo.name in CAMPOS_DE_ESTADO
    )


def _registrar(accion, instancia, detalle):
    usuario, nombre = quien()
    try:
        objeto = str(instancia)[:200]
    except Exception:
        objeto = f"#{instancia.pk}"
    RegistroCambio.objects.create(
        usuario=usuario,
        usuario_nombre=nombre,
        accion=accion,
        modelo=str(instancia._meta.verbose_name).capitalize(),
        objeto=objeto,
        detalle=detalle,
    )


@receiver(pre_save)
def guardar_valores_previos(sender, instance, raw=False, **kwargs):
    if raw or not _seguido(sender) or instance.pk is None:
        return
    instance._auditoria_previo = (
        sender._base_manager.filter(pk=instance.pk).values().first()
    )


@receiver(post_save)
def registrar_guardado(sender, instance, created, raw=False, update_fields=None, **kwargs):
    if raw or not _seguido(sender):
        return
    if update_fields and set(update_fields) <= CAMPOS_IGNORADOS:
        return
    if created:
        _registrar(RegistroCambio.Accion.CREACION, instance, _resumen(instance))
        return
    previo = getattr(instance, "_auditoria_previo", None)
    cambios = _diferencias(instance, previo, update_fields)
    if cambios:
        if _es_inhabilitacion(instance, previo, update_fields):
            accion = RegistroCambio.Accion.INHABILITACION
        else:
            accion = RegistroCambio.Accion.MODIFICACION
        _registrar(accion, instance, "; ".join(cambios))


@receiver(post_delete)
def registrar_eliminacion(sender, instance, **kwargs):
    if _seguido(sender):
        _registrar(RegistroCambio.Accion.ELIMINACION, instance, "")


@receiver(user_logged_in)
def registrar_ingreso(sender, request, user, **kwargs):
    RegistroCambio.objects.create(
        usuario=user,
        usuario_nombre=user.get_username(),
        accion=RegistroCambio.Accion.INGRESO,
        detalle="Inició sesión.",
    )


@receiver(user_login_failed)
def registrar_ingreso_fallido(sender, credentials=None, **kwargs):
    nombre = str((credentials or {}).get("username", ""))[:150]
    RegistroCambio.objects.create(
        usuario=None,
        usuario_nombre=nombre,
        accion=RegistroCambio.Accion.INGRESO_FALLIDO,
        detalle="Credenciales incorrectas o cuenta no habilitada.",
    )
