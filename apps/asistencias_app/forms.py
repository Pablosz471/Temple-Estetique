from django import forms
from apps.empleados_app.models import Empleado
from .models import RegistroAsistencia


class MarcarAsistenciaForm(forms.Form):
    empleado = forms.ModelChoiceField(queryset=Empleado.objects.filter(activo=True))
    accion = forms.ChoiceField(choices=[("ingreso", "Ingreso"), ("salida", "Salida")])


class DetalleAsistenciaForm(forms.ModelForm):
    class Meta:
        model = RegistroAsistencia
        fields = ("detalle",)
        widgets = {"detalle": forms.Textarea(attrs={"rows": 3})}
