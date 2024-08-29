from django.urls import path
from .views import UserListView, UserCreateView, UserUpdateView, DeletePersonView


app_name = 'users'

urlpatterns = [
    path("", UserListView.as_view(), name='users'),
    path("edit-user/<int:pk>/", UserUpdateView.as_view(), name='edit-user'),
    path("<int:pk>/delete/", DeletePersonView.as_view(), name='delete-person'),
    path('create/', UserCreateView.as_view(), name='create_user'),

]