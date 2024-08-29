from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['entry_date', 'exit_date', 'parking', 'price']  # No incluimos 'vehicle' ya que lo gestionamos en la vista
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date'}),
            'exit_date': forms.DateInput(attrs={'type': 'date'}),
            'parking': forms.HiddenInput(),
            'price': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            # Asumimos que solo hay un vehículo por usuario, o ajustar según sea necesario
            instance.user = self.user
            instance.vehicle = self.user.profile.vehicle  # Aquí se asume que el usuario tiene un perfil con un vehículo
        if commit:
            instance.save()
        return instance

