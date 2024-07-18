from django.urls import path
from preprint.views import *

# app_name = 'preprint'

urlpatterns = [
    path('mypage/', print_mypage, name='mypage'),
    path('payment_detail/', print_payment_detail, name='payment_detail'),
    path('print_detail/', print_detail, name="print_detail"),
    path('print_payment/', print_payment, name="print_payment"),
]