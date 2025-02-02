from django.contrib import admin
from .models import PassOrder, PassOrderPayment

# Register your models here.
# Pass Order Admin
class PassOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'pass_order_user', 'pass_order_price', 'pass_order_date', 'status', 'total_pages', 'is_takeout']
    search_fields = ['pass_order_user__username', 'pass_order_user__email']
    list_filter = ['status', 'pass_order_date']
    ordering = ['-pass_order_date']

# Pass Order Payment Admin
class PassOrderPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'pass_order', 'name', 'desired_amount', 'pay_status', 'is_paid_ok']
    search_fields = ['pass_order__pass_order_user__username', 'pass_order__pass_order_user__email']
    list_filter = ['pay_status']
    ordering = ['-id']

admin.site.register(PassOrder, PassOrderAdmin)
admin.site.register(PassOrderPayment, PassOrderPaymentAdmin)