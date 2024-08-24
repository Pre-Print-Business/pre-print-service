from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from json.decoder import JSONDecodeError
from rest_framework import status
from rest_framework.response import Response
from dj_rest_auth.registration.views import SocialLoginView
from .forms import SocialSignUpForm
from allauth.socialaccount.providers.google import views as google_view
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.models import SocialAccount
from users.models import User
from django.views.decorators.csrf import csrf_exempt

state = 'stsegsdfsdfsfd'
BASE_URL = "http://127.0.0.1:8000/" if settings.DEBUG else "https://preprintreserve.com/"
GOOGLE_CALLBACK_URI = BASE_URL + 'accounts/google/callback/'
KAKAO_CALLBACK_URI = BASE_URL + 'accounts/kakao/callback/'

def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = getattr(settings, "SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}&prompt=select_account")

@csrf_exempt
def google_callback(request):
    client_id = settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
    client_secret = settings.SOCIAL_AUTH_GOOGLE_SECRET
    code = request.GET.get('code')

    token_req = requests.post(
        f"https://oauth2.googleapis.com/token",
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': GOOGLE_CALLBACK_URI,
        }
    )
    token_req_json = token_req.json()
    access_token = token_req_json.get('access_token')
    id_token = token_req_json.get('id_token')

    if not access_token or not id_token:
        return JsonResponse({'err_msg': 'Failed to obtain access token or id token'}, status=status.HTTP_400_BAD_REQUEST)

    email_req = requests.get(
        f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}")
    email_req_json = email_req.json()
    email = email_req_json.get('email')

    if not email:
        return JsonResponse({'err_msg': 'Failed to retrieve email from token'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        login(request, user)
        return redirect('root')
    except User.DoesNotExist:
        request.session['email'] = email
        return redirect('social_signup')

# Kakao
def kakao_login(request):
    rest_api_key = settings.KAKAO_REST_API_KEY
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code&prompt=login"
    )

@csrf_exempt
def kakao_callback(request):
    rest_api_key = settings.KAKAO_REST_API_KEY
    redirect_uri = KAKAO_CALLBACK_URI
    code = request.GET.get("code")

    token_req = requests.get(
        f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={rest_api_key}&redirect_uri={redirect_uri}&code={code}")
    token_req_json = token_req.json()
    access_token = token_req_json.get("access_token")

    if not access_token:
        return JsonResponse({'err_msg': 'Failed to obtain access token'}, status=status.HTTP_400_BAD_REQUEST)

    profile_request = requests.get(
        "https://kapi.kakao.com/v2/user/me", headers={"Authorization": f"Bearer {access_token}"})
    profile_json = profile_request.json()
    kakao_account = profile_json.get('kakao_account')
    email = kakao_account.get('email')

    if not email:
        return JsonResponse({'err_msg': 'Failed to retrieve email from Kakao account'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        login(request, user)
        return redirect('root')
    except User.DoesNotExist:
        request.session['email'] = email
        return redirect('social_signup')

def social_signup(request):
    if request.method == 'POST':
        phone1 = request.POST.get('phone1')
        phone2 = request.POST.get('phone2')

        # phone1 또는 phone2 필드가 비어 있거나 4자리가 아닌 경우
        if not phone1 or not phone2 or len(phone1) != 4 or len(phone2) != 4:
            return render(request, 'accounts/social_signup.html', {
                'form': SocialSignUpForm(request.POST),
                'form_errors': {'phone': ["전화번호를 올바르게 입력해 주세요. (각각 4자리 숫자)"]},
            })

        full_phone = f"010-{phone1}-{phone2}"
        post_data = request.POST.copy()
        post_data['phone'] = full_phone
        
        form = SocialSignUpForm(post_data)

        if form.is_valid():
            email = request.session.get('email')
            user = form.save(commit=False)
            user.email = email
            user.set_password(None)
            user.save()
            login(request, user)
            return redirect('root')
        else:
            print("Form errors:", form.errors)
            return render(request, 'accounts/social_signup.html', {'form': form, 'form_errors': form.errors})
    else:
        form = SocialSignUpForm()
    return render(request, 'accounts/social_signup.html', {'form': form})

def print_signup(req):
    if req.method == 'GET':
        form = SignUpForm()
        context = {'form': form}
        return render(req, 'accounts/print_signup.html', context)
    else:
        form = SignUpForm(req.POST)
        if form.is_valid():
            instance = form.save()
            return redirect('main')
        else:
            return redirect('signup')
        
def print_login(req):
    if req.method == 'GET':
        return render(req, 'accounts/print_login.html', {'form': AuthenticationForm()})
    else:
        form = AuthenticationForm(req, req.POST)
        if form.is_valid():
            login(req, form.user_cache) 
            return redirect('root')
        else:
            return render(req, 'accounts/print_login.html', {'form': form})

def print_logout(req):
    if req.user.is_authenticated:
        logout(req)
    return redirect('root')
    