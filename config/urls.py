
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from preprint.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', print_main, name="main"),
    path('detail/', print_detail, name="detail"),
    path('payment/', print_payment, name="payment"),
    path('accounts/', include('accounts.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
