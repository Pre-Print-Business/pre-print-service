import csv
import os
import shutil

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.db import connection
from preprint.models import Order, OrderFile

class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def clear_today_orders_folder(self):
        shutil.rmtree("today_orders", ignore_errors=True)
        os.makedirs("today_orders")

    def handle(self, *args, **options):
        self.clear_today_orders_folder()

        with open("today_orders/today_orders.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['orderFile.id', 'orderFile.file', 'order.order_id', 'order.order_color', 'order.orderdate', 'order.order_user', 'user.username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            order_num = 1
            orders = Order.objects.all()
            for order in orders:
                order_files = OrderFile.objects.filter(order=order)

                for order_file in order_files:
                    if default_storage.exists(order_file.file.name):
                        original_path = order_file.file.path
                        filename = os.path.basename(order_file.file.name)
                        backup_path = os.path.join("today_orders", f"{order_file.id}{os.path.splitext(filename)[1]}")
                        shutil.copy(original_path, backup_path)

                    writer.writerow({
                        'orderFile.id': order_file.id,
                        'orderFile.file': order_file.file.name,
                        'order.order_id': order.id,
                        'order.order_color': order.order_color,
                        'order.orderdate': order.order_date,
                        'order.order_user': order.order_user.id,
                        'user.username': order.order_user.username,
                    })

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

class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def clear_today_orders_folder(self):
        shutil.rmtree("today_orders", ignore_errors=True)
        os.makedirs("today_orders")

    def handle(self, *args, **options):
        self.clear_today_orders_folder()

        with open("today_orders/today_orders.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['orderFile.id', 'orderFile.file', 'order.order_id', 'order.order_color', 'order.orderdate', 'order.order_user', 'user.username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            order_num = 1
            orders = Order.objects.all()
            for order in orders:
                order_files = OrderFile.objects.filter(order=order)

                for order_file in order_files:
                    if default_storage.exists(order_file.file.name):
                        original_path = order_file.file.path
                        filename = os.path.basename(order_file.file.name)
                        backup_path = os.path.join("today_orders", f"{order_file.id}{os.path.splitext(filename)[1]}")
                        shutil.copy(original_path, backup_path)

                    writer.writerow({
                        'orderFile.id': order_file.id,
                        'orderFile.file': order_file.file.name,
                        'order.order_id': order.id,
                        'order.order_color': order.order_color,
                        'order.orderdate': order.order_date,
                        'order.order_user': order.order_user.id,
                        'user.username': order.order_user.username,
                    })

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

class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def clear_today_orders_folder(self):
        shutil.rmtree("today_orders", ignore_errors=True)
        os.makedirs("today_orders")

    def handle(self, *args, **options):
        self.clear_today_orders_folder()

        with open("today_orders/today_orders.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['orderFile.id', 'orderFile.file', 'order.order_id', 'order.order_color', 'order.orderdate', 'order.order_user', 'user.username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            order_num = 1
            orders = Order.objects.all()
            for order in orders:
                order_files = OrderFile.objects.filter(order=order)

                for order_file in order_files:
                    if default_storage.exists(order_file.file.name):
                        original_path = order_file.file.path
                        filename = os.path.basename(order_file.file.name)
                        backup_path = os.path.join("today_orders", f"{order_file.id}{os.path.splitext(filename)[1]}")
                        shutil.copy(original_path, backup_path)

                    writer.writerow({
                        'orderFile.id': order_file.id,
                        'orderFile.file': order_file.file.name,
                        'order.order_id': order.id,
                        'order.order_color': order.order_color,
                        'order.orderdate': order.order_date,
                        'order.order_user': order.order_user.id,
                        'user.username': order.order_user.username,
                    })

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

class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def clear_today_orders_folder(self):
        shutil.rmtree("today_orders", ignore_errors=True)
        os.makedirs("today_orders")

    def handle(self, *args, **options):
        self.clear_today_orders_folder()

        with open("today_orders/today_orders.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['orderFile.id', 'orderFile.file', 'order.order_id', 'order.order_color', 'order.orderdate', 'order.order_user', 'user.username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            order_num = 1
            orders = Order.objects.all()
            for order in orders:
                order_files = OrderFile.objects.filter(order=order)

                for order_file in order_files:
                    if default_storage.exists(order_file.file.name):
                        original_path = order_file.file.path
                        filename = os.path.basename(order_file.file.name)
                        backup_path = os.path.join("today_orders", f"{order_file.id}{os.path.splitext(filename)[1]}")
                        shutil.copy(original_path, backup_path)

                    writer.writerow({
                        'orderFile.id': order_file.id,
                        'orderFile.file': order_file.file.name,
                        'order.order_id': order.id,
                        'order.order_color': order.order_color,
                        'order.orderdate': order.order_date,
                        'order.order_user': order.order_user.id,
                        'user.username': order.order_user.username,
                    })

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

class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def clear_today_orders_folder(self):
        shutil.rmtree("today_orders", ignore_errors=True)
        os.makedirs("today_orders")

    def handle(self, *args, **options):
        self.clear_today_orders_folder()

        with open("today_orders/today_orders.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['orderFile.id', 'orderFile.file', 'order.order_id', 'order.order_color', 'order.orderdate', 'order.order_user', 'user.username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            order_num = 1
            orders = Order.objects.all()
            for order in orders:
                order_files = OrderFile.objects.filter(order=order)

                for order_file in order_files:
                    if default_storage.exists(order_file.file.name):
                        original_path = order_file.file.path
                        filename = os.path.basename(order_file.file.name)
                        backup_path = os.path.join("today_orders", f"{order_file.id}{os.path.splitext(filename)[1]}")
                        shutil.copy(original_path, backup_path)

                    writer.writerow({
                        'orderFile.id': order_file.id,
                        'orderFile.file': order_file.file.name,
                        'order.order_id': order.id,
                        'order.order_color': order.order_color,
                        'order.orderdate': order.order_date,
                        'order.order_user': order.order_user.id,
                        'user.username': order.order_user.username,
                    })

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

class Command(BaseCommand):
    help = 'Backup and reset all orders and files'

    def clear_today_orders_folder(self):
        shutil.rmtree("today_orders", ignore_errors=True)
        os.makedirs("today_orders")

    def handle(self, *args, **options):
        self.clear_today_orders_folder()

        with open("today_orders/today_orders.csv", 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['orderFile.id', 'orderFile.file', 'order.order_id', 'order.order_color', 'order.orderdate', 'order.order_user', 'user.username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            order_num = 1
            orders = Order.objects.all()
            for order in orders:
                order_files = OrderFile.objects.filter(order=order)

                for order_file in order_files:
                    if default_storage.exists(order_file.file.name):
                        original_path = order_file.file.path
                        filename = os.path.basename(order_file.file.name)
                        backup_path = os.path.join("today_orders", f"{order_file.id}{os.path.splitext(filename)[1]}")
                        shutil.copy(original_path, backup_path)

                    writer.writerow({
                        'orderFile.id': order_file.id,
                        'orderFile.file': order_file.file.name,
                        'order.order_id': order.id,
                        'order.order_color': order.order_color,
                        'order.orderdate': order.order_date,
                        'order.order_user': order.order_user.id,
                        'user.username': order.order_user.username,
                    })

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
