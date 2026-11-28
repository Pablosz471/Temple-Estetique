from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.empleados_app.models import Empleado
from .models import RegistroAsistencia
from .services import cerrar_vencidas


class MarcarAsistenciaForm(forms.Form):
    empleado = forms.ModelChoiceField(queryset=Empleado.objects.filter(activo=True))
    accion = forms.ChoiceField(
        choices=[("ingreso", "Ingreso"), ("salida", "Salida"), ("reabrir", "Reabrir")]
    )


class IngresoAsistenciaForm(forms.ModelForm):
    class Meta:
        model = RegistroAsistencia
        fields = ("empleado",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["empleado"].queryset = Empleado.objects.filter(activo=True)

    def clean_empleado(self):
        cerrar_vencidas()
        empleado = self.cleaned_data["empleado"]
        if empleado.asistencias.filter(activo=True, fecha_hora_ingreso__date=timezone.localdate()).exists():
            raise ValidationError(f"{empleado} ya registró su asistencia hoy.")
        return empleado


class DetalleAsistenciaForm(forms.ModelForm):
    class Meta:
        model = RegistroAsistencia
        fields = ("detalle",)
        widgets = {"detalle": forms.Textarea(attrs={"rows": 3})}
