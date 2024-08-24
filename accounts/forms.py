from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'email', 'phone']

class SocialSignUpForm(forms.ModelForm):
    birth_year = forms.ChoiceField(
        choices=[(year, year) for year in range(1900, 2025)],
        label="Birth Year"
    )
    birth_month = forms.ChoiceField(
        choices=[(month, month) for month in range(1, 13)],
        label="Birth Month"
    )
    birth_day = forms.ChoiceField(
        choices=[(day, day) for day in range(1, 32)],
        label="Birth Day"
    )
    gender = forms.ChoiceField(
        choices=[('M', '남자'), ('F', '여자')],
        label="Gender"
    )

    email_opt_in = forms.BooleanField(
        label="Subscribe to Emails",
        required=False,
        initial=True  # 기본 체크 상태로 설정
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'phone', 'email_opt_in', 'birth_year', 'birth_month', 'birth_day', 'gender']
