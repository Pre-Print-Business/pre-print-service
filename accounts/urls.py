from django.urls import path
from .views import *

# app_name = 'accounts'

urlpatterns = [
    # basic
    path('signup/', print_signup, name='signup'),
    path('login/', print_login, name='login'),
    path('logout/', print_logout, name='logout'),
    path('social_signup/', social_signup, name='social_signup'),
    # google
    path('google/login/', google_login, name='google_login'),
    path('google/callback/', google_callback, name='google_callback'),
    # kakao
    path('kakao/login/', kakao_login, name='kakao_login'),
    path('kakao/callback/', kakao_callback, name='kakao_callback'),
]