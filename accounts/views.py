from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from users.models import User

# accounts/views.py
from allauth.socialaccount.models import SocialLogin
from allauth.account.utils import complete_signup
from .forms import SocialSignUpForm
from django.urls import reverse

# accounts/views.py
from allauth.socialaccount.models import SocialLogin
from allauth.account.utils import complete_signup
from .forms import SocialSignUpForm
from django.shortcuts import render, redirect

# accounts/views.py
from allauth.socialaccount.models import SocialLogin
from allauth.account.utils import complete_signup
from .forms import SocialSignUpForm
from django.shortcuts import render, redirect

def social_signup(request):
    if 'socialaccount_sociallogin' not in request.session:
        return redirect('account_login')

    sociallogin = SocialLogin.deserialize(request.session['socialaccount_sociallogin'])
    print(sociallogin.account.extra_data)  # 디버그 출력
    if request.method == 'POST':
        form = SocialSignUpForm(request.POST)
        if form.is_valid():
            sociallogin.user.username = form.cleaned_data['username']
            provider = sociallogin.account.provider

            # 소셜 로그인 제공자에 따라 이메일 정보 가져오기
            if provider == 'preprint-google':
                email = sociallogin.account.extra_data.get('email', '')
            elif provider == 'preprint-kakao':
                email = sociallogin.account.extra_data.get('kakao_account', {}).get('email', '')
            else:
                email = ''

            # 이메일 디버그 출력
            print(f'Provider: {provider}, Email: {email}')

            # 이메일을 설정하고 저장
            sociallogin.user.email = email
            sociallogin.user.phone = form.cleaned_data['phone']
            sociallogin.user.save()  # 명시적으로 사용자 저장
            sociallogin.save(request)
            
            # 사용자 저장 확인
            print(f'User saved: {sociallogin.user.email}')
            
            return complete_signup(request, sociallogin.user, 'optional', None)
    else:
        form = SocialSignUpForm()

    return render(request, 'accounts/social_signup.html', {'form': form})


# Create your views here.
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
            return redirect('accounts:signup')
        
def print_login(req):
    if req.method == 'GET':
        return render(req, 'accounts/print_login.html', {'form': AuthenticationForm()})
    else:
        form = AuthenticationForm(req, req.POST)
        if form.is_valid():
            login(req, form.user_cache) 
            return redirect('main')
        else:
            return render(req, 'accounts/print_login.html', {'form': form})

        
def print_logout(req):
    if req.user.is_authenticated:
        logout(req)
    return redirect('main')
    