from django import forms
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils import timezone
from apps.asistencias_app.models import RegistroAsistencia
from apps.empleados_app.models import Empleado
from .models import Servicio, ServicioRealizado


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ("nombre_servicio", "descripcion", "precio")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}
        help_texts = {"precio": "Precio vigente del servicio."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["precio"].validators.append(MinValueValidator(0))


class RegistrarServicioForm(forms.ModelForm):
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.none(),
        empty_label="Elegí un empleado",
    )

    class Meta:
        model = ServicioRealizado
        fields = ("empleado", "servicio", "observacion")
        labels = {"observacion": "Observación"}
        widgets = {"observacion": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        con_asistencia_abierta = RegistroAsistencia.objects.filter(
            fecha_hora_salida__isnull=True
        ).values("empleado_id")
        empleados = Empleado.objects.filter(estado="Activo", pk__in=con_asistencia_abierta)
        self.fields["empleado"].queryset = empleados

        if not empleados.exists():
            self.fields["empleado"].help_text = (
                "No hay empleados con asistencia en curso. Registrá primero su asistencia."
            )

        self.fields["servicio"].queryset = Servicio.objects.filter(activo=True)
        self.fields["servicio"].empty_label = "Elegí un servicio"
        self.fields["servicio"].label_from_instance = (
            lambda servicio: f"{servicio.nombre_servicio} — $ {servicio.precio}"
        )

    def clean_empleado(self):
        empleado = self.cleaned_data["empleado"]
        if not empleado.asistencias.filter(fecha_hora_salida__isnull=True).exists():
            raise forms.ValidationError(
                "Este empleado no tiene una asistencia en curso. Registrá su asistencia primero."
            )
        return empleado

    @transaction.atomic
    def save(self, commit=True):
        realizado = super().save(commit=False)
        empleado = self.cleaned_data["empleado"]
        realizado.Registro_asistencia = empleado.asistencias.select_for_update().get(
            fecha_hora_salida__isnull=True
        )
        realizado.fecha_hora = timezone.now()
        realizado.monto_servicio = realizado.servicio.precio
        realizado.save()
        return realizado


class ObservacionServicioForm(forms.ModelForm):
    class Meta:
        model = ServicioRealizado
        fields = ("observacion",)
        labels = {"observacion": "Observación"}
        widgets = {"observacion": forms.Textarea(attrs={"rows": 3})}
