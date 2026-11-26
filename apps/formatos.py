from django.utils import timezone


def fecha_hora(momento):
    return timezone.localtime(momento).strftime("%d/%m/%Y %H:%M")
