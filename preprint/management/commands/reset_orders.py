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


# from django.core.management.base import BaseCommand
# from django.core.files.storage import default_storage
# from django.db import connection
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
#                 order_file.delete()
#             order.delete()

#         with connection.cursor() as cursor:
#             cursor.execute("DELETE FROM sqlite_sequence WHERE name='preprint_order';")
#             cursor.execute("DELETE FROM sqlite_sequence WHERE name='preprint_orderfile';")
        
#         self.stdout.write(self.style.SUCCESS('Successfully reset all orders and files.'))

import csv
import os
import shutil

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.db import connection
from preprint.models import Order, OrderFile


class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def backup_user_info(self, order, order_num):
        user = order.order_user
        backup_path = os.path.join("today_orders", f"{order_num}번 주문 유저 정보.csv")
        with open(backup_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['user_id', 'username', 'email', 'phone']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerow({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
            })

    def backup_files(self, order_files, order_num):
        for order_file in order_files:
            if default_storage.exists(order_file.file.name):
                original_path = order_file.file.path
                filename = os.path.basename(order_file.file.name)
                backup_path = os.path.join("today_orders", filename)
                shutil.copy(original_path, backup_path)

    def handle(self, *args, **options):
        if not os.path.exists("today_orders"):
            os.makedirs("today_orders")

        orders = Order.objects.all()
        order_num = 1
        for order in orders:
            order_files = OrderFile.objects.filter(order=order)

            self.backup_user_info(order, order_num)
            self.backup_files(order_files, order_num)

            for order_file in order_files:
                if default_storage.exists(order_file.file.name):
                    default_storage.delete(order_file.file.name)
                order_file.delete()
            order.delete()
            order_num += 1

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='preprint_order';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='preprint_orderfile';")

        self.stdout.write(self.style.SUCCESS('Successfully backed up and reset all orders and files.'))
