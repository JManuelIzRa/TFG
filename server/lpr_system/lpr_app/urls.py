from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('staff/', views.HomeStaffView.as_view(), name='staff-home'),
    path('accounts/login/', views.LoginFormView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignupFormView.as_view(), name='signup'),    
    path('contact/', views.ContactFormView.as_view(), name='contact'),
    path(
        'change-password/',
        auth_views.PasswordChangeView.as_view(success_url='/'),
        name='change-password'
    ),
    path('book/', include('book.urls', namespace='book')),
]