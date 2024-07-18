# accounts/adapter.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        # 구글 로그인 후 추가 회원가입 페이지로 리디렉션
        request.session['socialaccount_sociallogin'] = sociallogin.serialize()
        raise ImmediateHttpResponse(redirect('social_signup'))
