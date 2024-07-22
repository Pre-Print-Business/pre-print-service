from django.urls import path
from .views import *

# app_name = 'accounts'

urlpatterns = [
    path('signup/', print_signup, name='signup'),
    path('login/', print_login, name='login'),
    path('logout/', print_logout, name='logout'),
    # test
    path('test/22', test, name="test"),
    path('google/login', google_login, name='google_login'),
    path('google/callback/', google_callback, name='google_callback'),
    path('google/login/finish/', GoogleLogin.as_view(), name='google_login_todjango'),
]