from rest_framework import serializers
from .models import LicensePlate
from parking.models import Parking

class LicensePlateSerializer(serializers.ModelSerializer):

    parking = serializers.PrimaryKeyRelatedField(queryset=Parking.objects.all(), required=False, allow_null=True)


    class Meta:
        model = LicensePlate
        fields = ['plate_number', 'parking', 'detection_image']

    def create(self, validated_data):
        
        return LicensePlate.objects.create(**validated_data)
    
class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()