from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django import forms
from django.db.models import Sum
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm
from django.shortcuts import render, redirect
from django.db.models import F, Avg

from django.utils.http import url_has_allowed_host_and_scheme

from .models import User
from .forms import UserCreationForm

from license_plate.models import LicensePlate
from book.models import Reservation
import datetime
from datetime import timedelta

import matplotlib.pyplot as plt

class HomeStaffView(LoginRequiredMixin, TemplateView):
    template_name = 'index_staff.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = datetime.date.today()

        # Contar las matrículas detectadas hoy
        total_vehicles_today_count = LicensePlate.objects.filter(entry_date=today).count()
        
        # Contar matrículas que siguen estando dentro del parking
        real_vehicles = LicensePlate.objects.filter(entry_date=today, exit_date__isnull=True).count()

        # Ganancias totales dia de hoy
        today_gains = LicensePlate.objects.filter(entry_date=today, exit_date__isnull=False).aggregate(total_sum=Sum('amount_paid'))['total_sum']
        
        if today_gains is None:
            today_gains = 0
        else:
            # Redondea el total a dos decimales
            today_gains = round(today_gains, 2)

        # Ganancias del mes
        # Obtén el mes y año actuales
        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year

        # Filtra por el mes y año actuales y suma el campo 'cost'
        month_gains = LicensePlate.objects.filter(entry_date__year=current_year, entry_date__month=current_month, exit_date__isnull=False).aggregate(total_sum=Sum('amount_paid'))['total_sum']
        if month_gains is None:
            month_gains = 0
        else:
            # Redondea el total a dos decimales
            month_gains = round(month_gains, 2)

        avg_duration = LicensePlate.objects.filter(exit_date__isnull=False).annotate(
            duration=F('exit_date') - F('entry_date')
        ).aggregate(Avg('duration'))['duration__avg']

        # Convertir el tiempo promedio en horas
        if avg_duration is not None:
            avg_duration_hours = avg_duration.total_seconds() / 3600
            avg_duration_hours = round(avg_duration_hours, 2)
        else:
            avg_duration_hours = 0

        reservations_today_count = Reservation.objects.filter(created_at=today).count()

        # Obtener la fecha actual
        today = datetime.date.today()

        # Calcular fechas anteriores
        dates = [today - timedelta(days=i) for i in range(1, 8)]

        dates_reversed = dates[::-1]

        # Lista auxiliar para almacenar las fechas en formato "dd/mm/yyyy"
        dates_formatted = [d.strftime("%d/%m/%Y") for d in dates_reversed]

        # Obtener el número total de matrículas para cada fecha
        plates_counts = []
        for d in dates_reversed:
            count = LicensePlate.objects.filter(entry_date=d).count()
            plates_counts.append(count)

        # Pasar los datos al contexto
        context['labels'] = dates_formatted
        context['data'] = plates_counts

        # Crear el gráfico
        plt.figure(figsize=(10, 6))
        plt.plot(dates, plates_counts, marker='o', linestyle='-')
        plt.title('Número total de matrículas detectadas en los últimos 7 días')
        plt.xlabel('Fecha')
        plt.ylabel('Número de matrículas')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Guardar el gráfico en un archivo
        graph_path = 'plates_graph.png'  # Cambia la ruta según tu configuración
        plt.savefig(graph_path)

        # Pasar la ruta del gráfico al contexto
        # context['graph_path'] = graph_path


        # Pasar el conteo al contexto
        context['plates_today_count'] = str(total_vehicles_today_count)
        context['real_vehicles'] = str(real_vehicles)
        context['today_gains'] = str(today_gains)
        context['month_gains'] = str(month_gains)
        context['avg_duration_hours'] = avg_duration_hours
        context['reservations_today_count'] = reservations_today_count


        return context

class HomeView(TemplateView):
    template_name = 'index.html'

class LoginFormView(FormView):
    form_class = AuthenticationForm
    template_name = 'login.html'
    success_url = reverse_lazy('home')

    #@csrf_protect
    def form_valid(self, form):
        """
        The user has provided valid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        can log him in.
        """
        login(self.request, form.get_user())

        user = form.get_user()

        # Verificar si hay un parámetro 'next' en la URL
        if 'next' in self.request.POST:
            return redirect(self.request.POST.get('next'))
        
        # Si no hay 'next', redirigir según el rol del usuario
        if user.is_admin or user.is_staff:
            self.success_url = reverse_lazy('staff-home')
        else:
            self.success_url = reverse_lazy('home')

        return HttpResponseRedirect(self.get_success_url())
    

class SignupFormView(FormView):
    form_class = UserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        return render(self.request, self.template_name, {'form': form})
    
class ContactFormView(FormView):
    form_class = ContactForm
    template_name = 'contacto.html'
    success_url = reverse_lazy('home')  # Redirigir a la vista 'home'

    def form_valid(self, form):
        """
        This method is called when valid form data has been POSTed.
        It should return an HttpResponse.
        """
        # Procesar los datos del formulario
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        phone = form.cleaned_data.get('phone', 'N/A')
        message = form.cleaned_data['message']

        # Construir el mensaje de correo
        subject = f"New Contact Form Submission from {name}"
        full_message = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"

        # Enviar el correo electrónico
        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
        )

        # Redirigir a la página de inicio con un mensaje de éxito en la sesión
        self.request.session['contact_success'] = True
        return redirect(self.success_url)