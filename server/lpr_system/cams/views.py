from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageUploadSerializer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Camera
from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import api_view
from .serializers import CameraSerializer
from django.conf import settings
import os
from django.http import FileResponse, Http404
from datetime import datetime
import time



# Create your views here.
@api_view(['POST'])
def connect(request):
    if request.method == 'POST':
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Agregar la IP a los datos del request
        data = request.data.copy()
        data['ip_address'] = ip

        serializer = CameraSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CameraView(LoginRequiredMixin, View):
    model = Camera
    template_name = 'cams/index.html'

    def get(self, request, *args, **kwargs):
        cameras = Camera.objects.all()  # Suponiendo que quieres obtener todos los objetos Camera
        context = {'cameras': cameras}
        return render(request, self.template_name, context)

class ImageUploadView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.validated_data['image']
            
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")

            name = f'uploads/current_frame_{current_time}.jpg'
            
            path = default_storage.save(name, ContentFile(image.read()))
            return Response({'message': 'Image uploaded successfully', 'path': path}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def get_active_cameras(request):
    cameras = Camera.objects.filter(is_active=True)
    cameras_list = list(cameras.values('id', 'ip_address', 'parking', 'direction'))
    return JsonResponse(cameras_list, safe=False)

def get_frame(request, camera_id):
    # Construir la ruta al archivo de imagen
    file_path = os.path.join(settings.MEDIA_ROOT, f'uploads/current_frame_{camera_id}.jpg')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
    else:
        raise Http404("Image not found")
    
def get_frame_no_signal(request):
    # Construir la ruta al archivo de imagen
    file_path = os.path.join(settings.MEDIA_ROOT, 'no_signal.jpg')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
    else:
        raise Http404("Image not found")

