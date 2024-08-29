from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from lpr_app.forms import UserCreationForm

from django.views.generic.base import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .forms import CreateAdminForm, CreateClientForm
from lpr_app.models import User
from django.core.paginator import (
    Paginator,
    EmptyPage,
    PageNotAnInteger,
)

# Create your views here.
class UserListView(LoginRequiredMixin, ListView):
    model = User
    paginate_by = 10
    template_name = 'users/index.html'

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
        qs = super().get_queryset()

        # Recuperar parámetros de búsqueda de la URL
        user_type = self.request.GET.get('user_type')
        firstname = self.request.GET.get('firstname')
        secondname = self.request.GET.get('secondname')
        username = self.request.GET.get('username')

        # Aplicar filtros según los parámetros recibidos
        if user_type:
            if user_type == 'client':
                qs = qs.filter(is_admin=False)
            elif user_type == 'admin':
                qs = qs.filter(is_admin=True)

        if firstname:
            qs = qs.filter(firstname__icontains=firstname)

        if secondname:
            qs = qs.filter(secondname__icontains=secondname)

        if username:
            qs = qs.filter(username__icontains=username)

        return qs.order_by('secondname', 'firstname')



class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserCreationForm
    template_name = 'users/modify_user.html'
    success_url = reverse_lazy('users:users')  # Redirige a la lista de usuarios después de la edición

    def get_context_data(self, **kwargs):
        # Primero, obtiene el contexto original de la superclase
        context = super().get_context_data(**kwargs)
        
        # Captura el `pk` de la URL
        user_pk = self.kwargs.get('pk')
        
        # Recupera el objeto del usuario específico
        user_instance = User.objects.get(pk=user_pk)
        
        # Añade la instancia del usuario al contexto, lo que asegurará que el formulario se prellene
        context['form'] = self.form_class(instance=user_instance)
        
        # También puedes añadir la instancia del usuario directamente si es necesario en la plantilla
        context['user'] = user_instance
        
        return context
    
class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'users/create_user.html'
    success_url = reverse_lazy('users:users')  # Redirige a la lista de usuarios después de la creación

    def form_valid(self, form):
        # Aquí puedes añadir cualquier lógica extra que necesites antes de guardar el formulario
        return super().form_valid(form)

class DeletePersonView(LoginRequiredMixin, DeleteView, SuccessMessageMixin):
    model = User
    success_url = reverse_lazy('users:users')
    template_name = 'users/index.html'
    success_message = "El usuario %(nombre)s %(apellidos)s ha sido eliminado correctamente."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message % self.get_object().__dict__)
        return super().delete(request, *args, **kwargs)
