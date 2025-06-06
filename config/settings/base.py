from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

from django.core.exceptions import ImproperlyConfigured
import json

secret_file = BASE_DIR / "secrets.json"
with open(secret_file) as file:
    secrets = json.loads(file.read())

def get_secrets(setting, secrets_dict=secrets):
    try:
        return secrets_dict[setting]
    except KeyError:
        error_msg = f'set the {setting} environment variable'
        raise ImproperlyConfigured(error_msg)
    

SECRET_KEY = get_secrets('SECRET')

SOCIAL_AUTH_GOOGLE_CLIENT_ID = get_secrets("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
SOCIAL_AUTH_GOOGLE_SECRET = get_secrets("SOCIAL_AUTH_GOOGLE_SECRET")
STATE = get_secrets("STATE")

KAKAO_REST_API_KEY = get_secrets("KAKAO_REST_API_KEY")

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
PROJECT_APPS = [
    'preprint',
    'users',
    'accounts',
    'passorder',
    'locker'
]
THIRD_PARTY_APPS = [
    # django-rest-framework
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',
    # django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.kakao',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

REST_USE_JWT = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ),
}

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'
 
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': get_secrets('ENGINE'),
        'NAME': get_secrets('NAME'),
        'USER': get_secrets('USER'),
        'PASSWORD': get_secrets('PASSWORD'),
        'HOST': get_secrets('HOST'),
        'PORT': get_secrets('PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

# 이거 해줘야 db도 현재 시간대로 들어감
USE_TZ = False
TIME_ZONE = 'Asia/Seoul'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# 포트원
INTERNAL_IPS = ["127.0.0.1"]
PORTONE_SHOP_ID = get_secrets('PORTONE_SHOP_ID')
PORTONE_API_KEY = get_secrets('PORTONE_API_KEY')
PORTONE_API_SECRET = get_secrets('PORTONE_API_SECRET')
PORTONE_WEBHOOK_IPS = get_secrets('PORTONE_WEBHOOK_IPS')

# JWT
REST_USE_JWT = True
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

# 구글 메일
APP_PASSWORD = get_secrets('APP_PASSWORD')