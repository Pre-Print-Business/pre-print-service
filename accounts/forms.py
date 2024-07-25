from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'email', 'phone']

class SocialSignUpForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'phone', 'email_opt_in']
