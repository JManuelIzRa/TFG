from django.db import models

class Parking(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    total_spaces = models.IntegerField()
    image = models.ImageField(upload_to='parking_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.location}"
