import os
import csv
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from preprint.models import Order, OrderFile

class Command(BaseCommand):
    help = 'Create CSV file of today\'s orders and organize files'

    def handle(self, *args, **kwargs):
        # 현재 시간과 하루 전 시간을 가져옵니다.
        now = timezone.now()
        start_time = now - timedelta(days=1)
        start_time = start_time.replace(hour=1, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=1, minute=0, second=0, microsecond=0)

        # 조건에 맞는 주문을 가져옵니다.
        orders = Order.objects.filter(order_date__gte=start_time, order_date__lte=end_time, locker_number__isnull=False)

        # CSV 파일을 저장할 경로를 지정합니다.
        output_dir = os.path.join(settings.MEDIA_ROOT, 'today_orders')
        os.makedirs(output_dir, exist_ok=True)

        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Orders: {orders}")


        # today_orders 폴더 안에 있는 모든 파일을 삭제합니다.
        for file_name in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file_name)
            os.remove(file_path)

        # CSV 파일 경로를 지정합니다.
        csv_file_path = os.path.join(output_dir, f'{now.strftime("%Y-%m-%d")}_orders.csv')

        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # 헤더 작성
            writer.writerow(['User ID', 'Username', 'Locker Number', 'Locker PW', 'Files'])

            for order in orders:
                # 관련된 파일 이름을 콤마로 구분하여 가져옵니다.
                related_files = OrderFile.objects.filter(order=order)
                file_names = ', '.join([os.path.basename(file.file.name) for file in related_files])

                writer.writerow([order.order_user.id, order.order_user.username, order.locker_number, order.order_pw, file_names])

        # media/files에 있는 모든 파일을 today_orders로 이동하고 media/files를 비웁니다.
        files_dir = os.path.join(settings.MEDIA_ROOT, 'files')
        if os.path.exists(files_dir):
            for file_name in os.listdir(files_dir):
                file_path = os.path.join(files_dir, file_name)
                if file_name.endswith('.pdf'):
                    os.rename(file_path, os.path.join(output_dir, file_name))
                else:
                    os.remove(file_path)

        self.stdout.write(self.style.SUCCESS('CSV creation and file organization complete.'))
