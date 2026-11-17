from django import forms
from django.core.validators import MinValueValidator
from .models import RegistroAsistencia


class RegistroAsistenciaForm(forms.ModelForm):
    class Meta:
        model = RegistroAsistencia
        fields = ("empleado", "fecha_hora_ingreso", "fecha_hora_salida", "comision_diaria", "detalle")
        widgets = {
            "fecha_hora_ingreso": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "fecha_hora_salida": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "detalle": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("fecha_hora_ingreso", "fecha_hora_salida"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["comision_diaria"].validators.append(MinValueValidator(0))
