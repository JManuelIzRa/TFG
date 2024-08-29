from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Campos que se muestran en la lista de usuarios
    list_display = ('username', 'password', 'email', 'firstname', 'secondname', 'is_staff', 'is_admin', 'is_active')
    
    # Campos por los que se puede filtrar
    list_filter = ('is_staff', 'is_admin', 'is_active', 'deleted', 'register_date')
    
    # Campos por los que se puede buscar
    search_fields = ('username', 'email', 'firstname', 'secondname', 'code')
    
    # Ordenación predeterminada de la lista
    ordering = ('username',)
    
    # Campos que se muestran en el formulario de edición del usuario
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('firstname', 'secondname', 'email', 'code')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('register_date',)}),
        (_('Status'), {'fields': ('deleted',)}),
    )
    
    # Campos que se muestran al crear un nuevo usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'firstname', 'secondname', 'email', 'is_staff', 'is_admin', 'is_active', 'code')}
        ),
    )

    # Indicar los campos que son de solo lectura
    readonly_fields = ('register_date',)
