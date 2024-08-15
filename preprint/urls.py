from django.urls import path
from preprint.views import *

urlpatterns = [
    path('guide/', guide, name="guide"),
    path('mypage/', print_mypage, name='mypage'),
    path('print_payment_list/', print_payment_list, name='print_payment_list'),
    path('print_detail/', print_detail, name="print_detail"),
    path('print_payment_ready/<int:order_id>/', print_payment_ready, name='print_payment_ready'),
    path('print_payment/', print_payment, name="print_payment"),
    path('retry_payment/', retry_payment, name="retry_payment"),
    path('payment_check/<int:order_pk>/<int:payment_pk>/', print_payment_check, name='print_payment_check'),
    path('print_payment_detail/<int:order_pk>/', print_payment_detail, name='print_payment_detail'),
    path('cancel_order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('webhook/', portone_webhook, name='webhook'),
]
