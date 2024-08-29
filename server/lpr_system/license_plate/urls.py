from django.urls import path
from .views import register_plate, LicensePlateListView, delete_license_plate, register_exit, generate_pdf, get_frame

app_name = 'license_plate'

urlpatterns = [
    path("", LicensePlateListView.as_view(), name='license_plate'),
    path('api/register/', register_plate, name='api_register_plate'),
    path('api/register_exit/', register_exit, name='register_exit'),
    path('eliminar/<int:pk>/', delete_license_plate, name='delete_license_plate'),
    path('generate-pdf/<int:pk>', generate_pdf, name='generate_pdf'),
    path('api/get_frame/<str:number_plate>/', get_frame, name='get_frame'),
]