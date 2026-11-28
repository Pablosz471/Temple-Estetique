from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from cuentas.models import Usuario
from .models import Empleado, Rol


class EmpleadoBaseForm(forms.ModelForm):
    """Campos comunes del empleado.

    Solo el superusuario puede elegir el rol Administrador. Sin `usuario_actual`
    se aplica la restricción.
    """

    class Meta:
        model = Empleado
        fields = ("nombre", "apellido", "dni", "telefono", "rol", "direccion")
        labels = {"dni": "DNI", "telefono": "Teléfono", "direccion": "Dirección"}
        widgets = {"direccion": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, usuario_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_actual = usuario_actual
        roles = [Rol.EMPLEADO]
        if usuario_actual is not None and usuario_actual.is_superuser:
            roles.append(Rol.ADMINISTRADOR)
        self.fields["rol"].queryset = Rol.objects.filter(nombre_rol__in=roles)
        self.fields["rol"].empty_label = None


def _campo_clave(etiqueta):
    return forms.CharField(
        label=etiqueta,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )


def _validar_claves(form, datos, usuario):
    """Las dos contraseñas coinciden y cumplen las reglas del sistema."""
    clave1, clave2 = datos.get("password1"), datos.get("password2")
    if clave1 and clave2 and clave1 != clave2:
        form.add_error("password2", "Las contraseñas no coinciden.")
    elif clave1:
        try:
            validate_password(clave1, usuario)
        except forms.ValidationError as error:
            form.add_error("password1", error)


class EmpleadoCrearForm(EmpleadoBaseForm):
    username = forms.CharField(label="Nombre de usuario", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    password1 = _campo_clave("Contraseña")
    password2 = _campo_clave("Repetir contraseña")

    field_order = [
        "username", "nombre", "apellido", "dni", "telefono",
        "email", "rol", "direccion", "password1", "password2",
    ]

    def clean_username(self):
        valor = self.cleaned_data["username"].strip().lower()
        if Usuario.objects.filter(username__iexact=valor).exists():
            raise forms.ValidationError("El nombre de usuario ya está en uso.")
        return valor

    def clean_email(self):
        valor = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=valor).exists():
            raise forms.ValidationError("El correo ya está registrado.")
        return valor

    def clean(self):
        datos = super().clean()
        provisorio = Usuario(
            username=datos.get("username", ""),
            email=datos.get("email", ""),
            first_name=datos.get("nombre", ""),
            last_name=datos.get("apellido", ""),
        )
        _validar_claves(self, datos, provisorio)
        return datos

    @transaction.atomic
    def save(self, commit=True):
        usuario = Usuario.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["nombre"],
            last_name=self.cleaned_data["apellido"],
            is_active=True,
            estado=Usuario.Estado.APROBADO,
        )
        empleado = super().save(commit=False)
        empleado.usuario = usuario
        empleado.save()
        return empleado


class RestablecerPasswordForm(forms.Form):
    password1 = _campo_clave("Nueva contraseña")
    password2 = _campo_clave("Repetir nueva contraseña")

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario

    def clean(self):
        datos = super().clean()
        _validar_claves(self, datos, self.usuario)
        return datos

    def save(self):
        self.usuario.set_password(self.cleaned_data["password1"])
        self.usuario.save(update_fields=["password"])
        return self.usuario


class EmpleadoEditarForm(EmpleadoBaseForm):
    email = forms.EmailField(label="Correo electrónico")

    field_order = ["nombre", "apellido", "dni", "telefono", "email", "rol", "direccion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].initial = self.instance.usuario.email

    def clean_email(self):
        valor = self.cleaned_data["email"].strip().lower()
        otros = Usuario.objects.exclude(pk=self.instance.usuario_id)
        if otros.filter(email__iexact=valor).exists():
            raise forms.ValidationError("Ese correo ya está registrado.")
        return valor

    def clean_activo(self):
        activo = self.cleaned_data["activo"]
        es_uno_mismo = self.usuario_actual and self.instance.usuario_id == self.usuario_actual.pk
        if es_uno_mismo and not activo:
            raise forms.ValidationError("No puedes inhabilitar tu propio perfil.")
        return activo


    @transaction.atomic
    def save(self, commit=True):
        empleado = super().save(commit=False)
        empleado.save()
        self.save_m2m()
        usuario = empleado.usuario
        usuario.email = self.cleaned_data["email"]
        usuario.first_name = empleado.nombre
        usuario.last_name = empleado.apellido
        usuario.save(update_fields=["email", "first_name", "last_name"])
        
        return empleado
