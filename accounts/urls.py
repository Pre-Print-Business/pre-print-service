from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('signup/', print_signup, name='signup'),
    path('login/', print_login, name='login'),
    path('logout/', print_logout, name='logout'),
]