# Create your models here.
from django.db import models
from lpr_app.models import User
from parking.models import Parking
from datetime import datetime, date
from decimal import Decimal



class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE)
    vehicle = models.CharField(max_length=50)
    entry_date = models.DateTimeField()
    exit_date = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    '''def __str__(self):
        return f"Reservation for {self.user.username} at {self.parking.name} from {self.start_date} to {self.end_date}"'''

    def save(self, *args, **kwargs):
        entry_date = datetime.strptime(self.entry_date, '%Y-%m-%d')
        exit_date = datetime.strptime(self.exit_date, '%Y-%m-%d')
        # Calculate the price based on the duration and the parking price per hour
        duration = (exit_date - entry_date).total_seconds() / 3600
        duration = float(duration)  # Asegúrate de que sea un float
        price_per_hour = Decimal(self.parking.price_per_hour)  # Convertir a Decimal

        cost = Decimal(duration) * price_per_hour

        created_at = datetime.today()

        self.price = cost
        self.created_at = created_at
        super().save(*args, **kwargs)
