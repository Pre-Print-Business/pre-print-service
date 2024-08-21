from django.contrib import admin
from .models import Order, OrderFile, OrderPayment

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_user', 'order_price', 'order_date', 'locker_number', 'status']
    search_fields = ['order_user__username', 'order_user__email']
    list_filter = ['status', 'order_date']
    ordering = ['-order_date']

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderFile)
admin.site.register(OrderPayment)
