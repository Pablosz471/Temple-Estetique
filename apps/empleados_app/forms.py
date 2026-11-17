from django import forms
from django.db.models import Q
from cuentas.models import Usuario
from .models import Empleado, Rol


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ("nombre_rol", "descripcion")


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = (
            "usuario", "rol", "nombre", "apellido", "dni", "telefono",
            "direccion", "estado", "foto_empleado", "especialidad",
        )
        widgets = {"direccion": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        actual = self.instance.usuario_id if self.instance.pk else None
        usuarios = Usuario.objects.filter(is_active=True, estado="aprobado").filter(
            Q(empleado__isnull=True) | Q(pk=actual)
        ).order_by("username")
        self.fields["usuario"].queryset = usuarios
        self.fields["usuario"].help_text = "Solo aparecen cuentas aprobadas y activas que todavía no están vinculadas a un empleado."


class BuscarForm(forms.Form):
    q = forms.CharField(required=False, max_length=100)
