from django.contrib import admin
from .models import Locker, LockerOrder, LockerOrderPayment

# Locker Admin
class LockerAdmin(admin.ModelAdmin):
    list_display = ['id', 'locker_number', 'is_using']
    search_fields = ['locker_number']
    list_filter = ['is_using']
    ordering = ['locker_number']

# Locker Order Admin
class LockerOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_user', 'locker', 'order_price', 'order_start_date', 'order_end_date', 'rental_period', 'status']
    search_fields = ['user__username', 'user__email']
    list_filter = ['status', 'order_start_date', 'order_end_date']
    ordering = ['-order_start_date']

# Locker Order Payment Admin
class LockerOrderPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'locker_order', 'name', 'desired_amount', 'pay_status', 'is_paid_ok']
    search_fields = ['locker_order__user__username', 'locker_order__user__email']
    list_filter = ['pay_status']
    ordering = ['-id']


# Register models in Django admin
admin.site.register(Locker, LockerAdmin)
admin.site.register(LockerOrder, LockerOrderAdmin)
admin.site.register(LockerOrderPayment, LockerOrderPaymentAdmin)