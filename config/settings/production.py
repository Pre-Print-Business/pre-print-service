from .base import *

DEBUG = False


### EC2
# ALLOWED_HOSTS = ['13.125.43.166', 'preprintreserve.com', 'www.preprintreserve.com']
# CSRF_TRUSTED_ORIGINS = ['http://13.125.43.166', 'https://13.125.43.166', 'https://preprintreserve.com', 'https://www.preprintreserve.com']

### LIGHTsail
ALLOWED_HOSTS = ['43.202.226.155', 'preprintreserve.com', 'www.preprintreserve.com']
CSRF_TRUSTED_ORIGINS = ['http://43.202.226.155', 'https://43.202.226.155', 'https://preprintreserve.com', 'https://www.preprintreserve.com']


INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

STATIC_ROOT = BASE_DIR / 'static'

# LOG_FILE = '/home/ubuntu/pre-print-service/log/django.log'
LOG_FILE = BASE_DIR / 'log' / 'django.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILE,
            'when': "midnight",  # 매 자정마다
            'backupCount': 31,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    # Loggers (where does the log come from)
    'loggers': {
        'repackager': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.server': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console', 'logfile'],
            'level': 'WARN',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['logfile'],
            'propagate': True,
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['logfile'],
            'propagate': False,
        },
        'django.request': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}