from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import LicensePlate
from parking.models import Parking
from .serializers import LicensePlateSerializer
from .serializers import ImageUploadSerializer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import (
    Paginator,
    EmptyPage,
    PageNotAnInteger,
)
import os
import pdfkit
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
from django.views import View
from django.template.loader import render_to_string
from django.conf import settings
import datetime
from datetime import timedelta
from django.http import FileResponse, Http404


@api_view(['POST'])
def register_plate(request):
    if request.method == 'POST':
        serializer = LicensePlateSerializer(data=request.data)
        if serializer.is_valid():
            plate_number = serializer.validated_data['plate_number']
            
            # Verifica si ya existe un objeto con el mismo número de matrícula y campo de salida como null
            existing_plate = LicensePlate.objects.filter(plate_number=plate_number, exit_date__isnull=True).first()
            if existing_plate:
                return Response({'message': 'A plate with this number already exists and is in the parking at that moment.'}, status=status.HTTP_200_OK)
            

            image = serializer.validated_data['detection_image']
            
            name = f'uploads/license_plate_{plate_number}.jpg'
            
            path = default_storage.save(name, ContentFile(image.read()))

            # Verifica si se proporciona un parking en los datos de la solicitud
            parking = serializer.validated_data.get('parking')
            
            # Asigna un parking predeterminado si no se especifica
            if not parking:
                parking = Parking.objects.first()  # O elige un parking basado en otros criterios
            
            # Guarda el nuevo objeto LicensePlate con el parking asignado
            license_plate = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_exit(request):
    if request.method == 'POST':
        serializer = LicensePlateSerializer(data=request.data)
        if serializer.is_valid():
            plate_number = serializer.validated_data['plate_number']
            
            # Verifica si ya existe un objeto con el mismo número de matrícula y campo de salida como null
            existing_plate = LicensePlate.objects.filter(plate_number=plate_number, exit_date__isnull=True).first()
            if existing_plate:
                
                exit_date = datetime.date.today()
                exit_time = datetime.datetime.now().time()

                existing_plate.exit_date = exit_date
                existing_plate.exit_time = exit_time

                # Calcula cuanto tiene que pagar por el tiempo que ha pasado en el parking
                entry_datetime = datetime.datetime.combine(existing_plate.entry_date, existing_plate.entry_time)
                exit_datetime = datetime.datetime.combine(exit_date, exit_time)
                time_spent = exit_datetime - entry_datetime

                # Convertir el tiempo transcurrido a minutos
                hours_spent = time_spent.total_seconds() / 60
                
                # Aplicamos nuestra tarifa
                rate_per_minute = 0.1
                existing_plate.amount_paid = rate_per_minute * hours_spent

                existing_plate.save()

                return Response({'message': 'Exit time registered successfully'}, status=status.HTTP_200_OK)
            
            return Response({'error': 'No entry record found for this plate number.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@require_POST
def delete_license_plate(request, pk):
    license_plate = get_object_or_404(LicensePlate, pk=pk)
    license_plate.delete()
    return redirect('license_plate:license_plate')
    
def get_frame(request, number_plate):
    # Construir la ruta al archivo de imagen
    file_path = os.path.join(settings.MEDIA_ROOT, f'license_plate_images/{number_plate}.jpg')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
    else:
        raise Http404("Image not found")

class LicensePlateListView(LoginRequiredMixin, ListView):
    model = LicensePlate
    paginate_by = 10
    template_name = 'license-plate-history/index.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Paginación
        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            page_obj = paginator.get_page(page)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['object_list'] = page_obj.object_list
        
        return context

    def get_queryset(self):
        plate_number = self.request.GET.get('plate_number')
        entry_date = self.request.GET.get('entry_date')
        exit_date = self.request.GET.get('exit_date')
        filter_type = self.request.GET.get('filter')
        
        # Inicia el queryset con todos los registros
        data = LicensePlate.objects.all()
        
        # Filtra por matrícula si se proporciona
        if plate_number:
            data = data.filter(plate_number__icontains=plate_number)
        
        # Filtra por rango de fechas si se proporciona
        if entry_date:
            data = data.filter(entry_date__gte=entry_date)
        if exit_date:
            data = data.filter(exit_date__lte=exit_date)
        
        # Filtra por tipo de filtro (día, semana, mes)
        if filter_type:
            now = datetime.today()
            if filter_type == 'day':
                start_date = now - timedelta(days=1)
            elif filter_type == 'week':
                start_date = now - timedelta(weeks=1)
            elif filter_type == 'month':
                start_date = now - timedelta(days=30)
            data = data.filter(entry_date__gte=start_date)
        
        # Ordena los resultados por fecha de entrada
        data = data.order_by('-entry_date')
        return data
    
def generate_pdf(request, pk):
    license_plate = get_object_or_404(LicensePlate, pk=pk)    
    
    plate_number = license_plate.plate_number
    entry_date = license_plate.entry_date
    exit_date = license_plate.exit_date
    entry_time = license_plate.entry_time
    exit_time = license_plate.exit_time
    amount_paid = license_plate.amount_paid

    amount_before_tax = round(float(amount_paid * 100 /121), 2)

    tax_amount = round(float(amount_before_tax)*0.21, 2)

    context = {
        'plate_number': plate_number,
        'entry_date': entry_date,
        'exit_date': exit_date,
        'entry_time': entry_time,
        'exit_time': exit_time,
        'total_amount': amount_paid,
        'tax_rate':21,
        'amount_before_tax':amount_before_tax,
        'tax_amount':tax_amount,
    }

    # Renderiza la plantilla HTML
    html_string = render_to_string('license-plate-history/plantilla-factura.html', context)

    # Configuración de pdfkit para usar el ejecutable local de wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)

    # Genera el PDF
    pdf_file = pdfkit.from_string(html_string, False, configuration=config)

    # Retorna el PDF como respuesta HTTP
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="archivo.pdf"'

    return response