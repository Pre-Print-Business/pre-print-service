
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from preprint.views import *
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('dj_rest_auth.urls')),
    path('preprint/', include('preprint.urls')),
    path('',  TemplateView.as_view(template_name="print_main.html"), name="root"),
    # 웹사이트 운영 문서 안내
    path('document_privacy_policy', TemplateView.as_view(template_name="documents/document_privacy_policy.html"), name="document_privacy_policy"),
    path('document_terms_of_service', TemplateView.as_view(template_name="documents/document_terms_of_service.html"), name="document_terms_of_service"),
    path('document_payment_refund_policy', TemplateView.as_view(template_name="documents/document_payment_refund_policy.html"), name="document_payment_refund_policy"),
    path('document_customer_support_policy', TemplateView.as_view(template_name="documents/document_customer_support_policy.html"), name="document_customer_support_policy"),
    path('document_business_information', TemplateView.as_view(template_name="documents/document_business_information.html"), name="document_business_information"),
    path('document_ecommerce_compliance', TemplateView.as_view(template_name="documents/document_ecommerce_compliance.html"), name="document_ecommerce_compliance")
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
