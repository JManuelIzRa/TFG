from django.urls import path
from .views import UserListView, AdminCreateView, UserUpdateView, DeletePersonView


app_name = 'users'

urlpatterns = [
    path("", UserListView.as_view(), name='users'),
    path("add/admin/", AdminCreateView.as_view(), name='add-user'),
    path("edit-user/<int:pk>/", UserUpdateView.as_view(), name='edit-user'),
    path("<int:pk>/delete/", DeletePersonView.as_view(), name='delete-person'),
]