from django import forms
from lpr_app.models import User


class CreateAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    repeat_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'firstname', 'secondname', 'username', 'password', 'repeat_password', 'email', 'is_admin'
        ]

    def clean(self):
        cleaned_data = self.cleaned_data
        password = cleaned_data['password']
        repeat_password = cleaned_data['repeat_password']

        if password != repeat_password:
            raise forms.ValidationError('Las contraseñas deben de ser idénticas')
        return cleaned_data


class CreateClientForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'firstname', 'secondname', 'username', 'email'
        ]