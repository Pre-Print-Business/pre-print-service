# from django.core.management.base import BaseCommand
# from django.core.files.storage import default_storage
# from preprint.models import Order, OrderFile  

# class Command(BaseCommand):
#     help = 'Reset all orders and files'

#     def handle(self, *args, **options):
#         orders = Order.objects.all()
        
#         for order in orders:
#             order_files = OrderFile.objects.filter(order=order)
            
#             for order_file in order_files:
#                 if default_storage.exists(order_file.file.name):
#                     default_storage.delete(order_file.file.name)
            
#             order.delete()

#         self.stdout.write(self.style.SUCCESS('Successfully reset all orders and files.'))


from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.db import connection
from preprint.models import Order, OrderFile  

class Command(BaseCommand):
    help = 'Reset all orders and files'

    def handle(self, *args, **options):
        orders = Order.objects.all()
        for order in orders:
            order_files = OrderFile.objects.filter(order=order)
            for order_file in order_files:
                if default_storage.exists(order_file.file.name):
                    default_storage.delete(order_file.file.name)
                order_file.delete()
            order.delete()

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='preprint_order';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='preprint_orderfile';")
        
        self.stdout.write(self.style.SUCCESS('Successfully reset all orders and files.'))
