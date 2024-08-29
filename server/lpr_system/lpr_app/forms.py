from django import forms
from .models import User  # Asegúrate de importar tu modelo
from django.utils.translation import gettext as _


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['firstname', 'secondname', 'username', 'email', 'password1', 'password2', 'is_active', 'is_staff']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Las contraseñas no coinciden"))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True

        if commit:
            user.save()

        if user.check_password(self.cleaned_data["password1"]):
            print("La contraseña se guardó correctamente.")
        else:
            print("Error al guardar la contraseña.")
        return user

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label=_("Nombre"))
    email = forms.EmailField(label=_("Correo electrónico"))
    phone = forms.CharField(max_length=20, required=False, label=_("Número de teléfono (Opcional)"))
    message = forms.CharField(widget=forms.Textarea, label=_("Mensaje"))