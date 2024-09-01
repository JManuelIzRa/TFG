from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Parking, Reservation
from .forms import ReservationForm
from license_plate.models import LicensePlate
from django.views.generic.edit import FormView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from decimal import Decimal
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import get_template

class BookView(LoginRequiredMixin, View):
    template_name = 'bookings.html'
    
    def get(self, request):
        query = request.GET.get('location')
        entry_date = request.GET.get('entry_date')
        exit_date = request.GET.get('exit_date')
        
        if query and entry_date and exit_date:
            parkings = Parking.objects.filter(location__icontains=query)

            for parking in parkings:
                current_vehicles_count = LicensePlate.objects.filter(
                    parking=parking,
                    entry_date__lte=entry_date,
                    exit_date__isnull=True
                ).count()

                parking.available_spots = parking.total_spaces - current_vehicles_count
            
            # Filtrar solo los parkings que tienen disponibilidad
            parkings = [parking for parking in parkings if parking.available_spots > 0]
        else:
            parkings = []

        context = {
            'parkings': parkings,
        }

        return render(request, self.template_name, context)

class MakeReservationView(FormView):
    form_class = ReservationForm
    template_name = 'empty.html'  # Esta plantilla está vacía porque no necesitamos mostrar nada al usuario

    def post(self, request, *args, **kwargs):
        parking_id = request.POST.get('parking_id')
        entry_date = request.POST.get('entry_date')
        exit_date = request.POST.get('exit_date')
        vehicle = request.POST.get('vehicle')

        parking = get_object_or_404(Parking, id=parking_id)

        # Crear una reserva
        reservation = Reservation(
            parking=parking,
            user=request.user,
            entry_date=entry_date,
            exit_date=exit_date,
            vehicle=vehicle,  # Asegúrate de obtener el valor del vehículo del formulario o de otro lugar
        )
        reservation.save()
        send_user_mail(request.user, reservation, 0)

        success_url = reverse('book:book')  # Ajusta la URL de redirección según tu configuración
        return HttpResponseRedirect(f"{success_url}?message=success")

class ReservationSuccessView(LoginRequiredMixin, View):
    template_name = 'reservation_success.html'

    def get(self, request):
        return render(request, self.template_name)

class ManageReservationsView(LoginRequiredMixin, ListView):
    model = Reservation
    paginate_by = 10  
    template_name = 'book-history/index.html'
    # Ajusta esto a tu template

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
        plate_number = self.request.GET.get('vehicle')
        entry_date = self.request.GET.get('entry_date')
        exit_date = self.request.GET.get('exit_date')

        filter_type = self.request.GET.get('filter')
        
        data = Reservation.objects.filter(user=self.request.user)  # Filtrar por usuario actual
        
        if plate_number:
            data = data.filter(vehicle__icontains=plate_number)
        
        if entry_date:
            data = data.filter(entry_date__gte=entry_date)

        if exit_date:
            data = data.filter(exit_date__lte=exit_date)
        
        data = data.order_by('-entry_date')
        return data


class EditReservationView(LoginRequiredMixin, View):
    template_name = 'book-history/edit_booking.html'
    success_url = reverse_lazy('book:manage_reservations')

    def get(self, request, *args, **kwargs):
        # Obtener la reserva existente
        reservation = get_object_or_404(Reservation, pk=self.kwargs['pk'])
        form = ReservationForm(instance=reservation)
        return render(request, self.template_name, {'form': form, 'reservation': reservation})

    def post(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=self.kwargs['pk'])
        # Obtener los datos enviados por POST
        entry_date = request.POST.get('entry_date')
        exit_date = request.POST.get('exit_date')

        reservation.entry_date = entry_date
        reservation.exit_date = exit_date
        
        reservation.save()
        send_user_mail(request.user, reservation, 1)

        # Redirigir a la URL de éxito con un mensaje de éxito
        return HttpResponseRedirect(f"{self.success_url}?message=success")

class DeleteReservationView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'book-history/index.html'
    success_message = "La reserva ha sido eliminada correctamente."

    success_url = reverse_lazy('book:manage_reservations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservation'] = self.get_object()

        return context

def send_user_mail(user, reservation, tipo):
    if tipo == 0:
        subject = f'Confirmación Reserva #{reservation.pk}'
    elif tipo == 1:
        subject = f'Modificación Reserva #{reservation.pk}'
    else:
        subject = f'Eliminación Reserva #{reservation.pk}'

    template = get_template('book-history/confirmacion_reserva.html')

    content = template.render({
        'user': user,
        'username' :user.firstname + ' ' + user.secondname,
        'parking_name': reservation.parking,
        'parking_location': reservation.parking.location,
        'vehicle' : '9444JVL',
        'entry_date': reservation.entry_date,
        'exit_date': reservation.exit_date,
        'price' : reservation.price
    })
    print(user.email)
    message = EmailMultiAlternatives(subject, #Titulo
                                    '',
                                    settings.EMAIL_HOST_USER, #Remitente
                                    [user.email]) #Destinatario

    message.attach_alternative(content, 'text/html')
    message.send()