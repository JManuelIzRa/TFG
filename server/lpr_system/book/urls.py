from django.urls import path
from .views import  BookView, MakeReservationView, ReservationSuccessView, ManageReservationsView, EditReservationView, DeleteReservationView

app_name = 'book'

urlpatterns = [
    path('', BookView.as_view(), name='book'),
    path('make_reservation/', MakeReservationView.as_view(), name='make_reservation'),    path('reservation_success/', ReservationSuccessView.as_view(), name='reservation_success'),
    path('manage_reservations/', ManageReservationsView.as_view(), name='manage_reservations'),
    path('edit_reservation/<int:pk>/', EditReservationView.as_view(), name='edit_reservation'),
    path('delete_reservation/<int:pk>/', DeleteReservationView.as_view(), name='delete_reservation'),
]
