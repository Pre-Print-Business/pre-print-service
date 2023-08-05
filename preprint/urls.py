from django.urls import path
from preprint.views import *

app_name = 'preprint'

urlpatterns = [
    path('mypage/', print_mypage, name='mypage'),
    path('payment_detail/', print_payment_detail, name='payment_detail'),
]