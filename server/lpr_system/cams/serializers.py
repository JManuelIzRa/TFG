from rest_framework import serializers
from .models import Camera

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

class CameraSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Camera
        fields = ['ip_address', 'parking', 'direction', 'is_active']