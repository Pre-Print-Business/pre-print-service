from .base import *

import pymysql  
pymysql.install_as_MySQLdb()

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]