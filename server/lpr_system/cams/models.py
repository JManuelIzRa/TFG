from django.db import models

# Create your models here.
class Camera(models.Model):
    ip_address = models.GenericIPAddressField()
    parking = models.CharField(max_length=100)
    direction = models.CharField(max_length=50, choices=[('Entry', 'Entrada'), ('Exit', 'Salida')])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.parking} - {self.direction} - {self.ip_address}"
