import os
import csv
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from preprint.models import Order, OrderFile, OrderPayment, ArchivedOrder, ArchivedOrderFile, ArchivedOrderPayment

class Command(BaseCommand):
    help = 'Create CSV file of today\'s orders, organize files, rename PDF files, and archive the data'

    def handle(self, *args, **kwargs):
        now = timezone.localtime()
        start_time = now - timedelta(days=1)
        start_time = start_time.replace(hour=1, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=1, minute=0, second=0, microsecond=0)

        orders = Order.objects.filter(order_date__gte=start_time, order_date__lte=end_time, locker_number__isnull=False)

        output_dir = os.path.join(settings.MEDIA_ROOT, 'today_orders')
        os.makedirs(output_dir, exist_ok=True)

        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Orders: {orders}")

        # 기존 파일 삭제
        for file_name in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file_name)
            os.remove(file_path)

        csv_file_path = os.path.join(output_dir, f'{now.strftime("%Y-%m-%d")}.csv')

        file_counter = 1
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['User ID', 'Username', 'Locker Number', 'Locker PW', 'Color', 'Files'])

            for order in orders:
                related_files = OrderFile.objects.filter(order=order)
                new_file_names = []

                for file in related_files:
                    original_file_name = os.path.basename(file.file.name)
                    new_file_name = f"{file_counter}.pdf"
                    original_file_path = os.path.join(settings.MEDIA_ROOT, 'files', original_file_name)
                    new_file_path = os.path.join(output_dir, new_file_name)

                    # 파일 이름을 숫자로 변경하면서 이동
                    if os.path.exists(original_file_path):
                        os.rename(original_file_path, new_file_path)
                        new_file_names.append(new_file_name)
                        file_counter += 1

                writer.writerow([
                    order.order_user.id, 
                    order.order_user.username, 
                    order.locker_number, 
                    order.order_pw, 
                    order.order_color,  
                    ', '.join(new_file_names)  # 여러 개의 파일 이름을 ","로 구분하여 기록
                ])

        self.stdout.write(self.style.SUCCESS('CSV creation, file renaming, and file organization complete.'))
        all_orders = Order.objects.all()
        self.archive_orders(all_orders)

    def archive_orders(self, orders):
        for order in orders:
            archived_order = ArchivedOrder.objects.create(
                order_user=order.order_user,
                order_price=order.order_price,
                order_pw=order.order_pw,
                order_color=order.order_color,
                order_date=order.order_date,
                locker_number=order.locker_number,
                status=order.status,
                total_pages=order.total_pages,
            )
            related_files = OrderFile.objects.filter(order=order)
            for file in related_files:
                ArchivedOrderFile.objects.create(
                    order=archived_order,
                    file=file.file,
                )
            related_payments = OrderPayment.objects.filter(order=order)
            for payment in related_payments:
                ArchivedOrderPayment.objects.create(
                    order=archived_order,
                    meta=payment.meta,
                    uid=payment.uid,
                    name=payment.name,
                    desired_amount=payment.desired_amount,
                    buyer_name=payment.buyer_name,
                    buyer_email=payment.buyer_email,
                    pay_method=payment.pay_method,
                    pay_status=payment.pay_status,
                    is_paid_ok=payment.is_paid_ok,
                )
            order.delete()
        self.stdout.write(self.style.SUCCESS('Orders, related files, and payments have been archived.'))
