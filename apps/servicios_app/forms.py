from django import forms
from django.core.validators import MinValueValidator
from apps.asistencias_app.models import RegistroAsistencia
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


class ServicioRealizadoForm(forms.ModelForm):
    class Meta:
        model = ServicioRealizado
        fields = ("Registro_asistencia", "servicio", "fecha", "monto_servicio", "observacion")
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Registro_asistencia"].required = True
        if self.instance.pk and not self.instance.Registro_asistencia_id:
            self.fields["Registro_asistencia"].queryset = RegistroAsistencia.objects.filter(
                empleado_id=self.instance.empleado_id,
                fecha_hora_ingreso__date=self.instance.fecha,
            )
            self.fields["Registro_asistencia"].help_text = (
                "Para conservar la relación, elegí la asistencia del mismo empleado y día. "
                "Si no aparece, registrá esa asistencia primero."
            )
        self.fields["monto_servicio"].validators.append(MinValueValidator(0))

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.empleado = self.cleaned_data["Registro_asistencia"].empleado
        if commit:
            instance.save()
            self.save_m2m()
        return instance
