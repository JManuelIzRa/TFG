from django.db import models
from parking.models import Parking
import datetime

def get_default_parking():
    # Devuelve el primer objeto Parking, o None si no hay ninguno
    return Parking.objects.first()

# Create your models here.
class LicensePlate(models.Model):
    plate_number = models.CharField(max_length=10, null=False)
    
    entry_date = models.DateField(default=datetime.date.today)
    entry_time = models.TimeField(default=datetime.datetime.now().time())
    
    exit_date = models.DateField(null=True)
    exit_time = models.TimeField(null=True)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, null=True, default=get_default_parking)

    detection_image = models.ImageField(upload_to='license_plate_images/', null=True, blank=True)

    db_table = 'license_plate'

