from django.urls import path
from .views import ImageUploadView, get_active_cameras, CameraView, connect, get_frame, get_frame_no_signal

app_name = 'cams'

urlpatterns = [
    path("", CameraView.as_view(), name='cams'),
    path('api/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('api/active-cameras/', get_active_cameras, name='get_active_cameras'),
    path('api/connect', connect, name='connect'),
    path('api/get_frame/<int:camera_id>/', get_frame, name='get_frame'),
    path('api/get_frame_no_signal/', get_frame_no_signal, name='get_frame_no_signal'),

]