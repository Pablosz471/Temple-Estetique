from django import forms
from django.core.validators import MinValueValidator
from .models import RegistroMensual


class RegistroMensualForm(forms.ModelForm):
    class Meta:
        model = RegistroMensual
        fields = ("empleado", "mes", "anio", "total_generado", "total_comisiones")
        widgets = {"mes": forms.Select(choices=[(i, i) for i in range(1, 13)])}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("total_generado", "total_comisiones"):
            self.fields[name].validators.append(MinValueValidator(0))
