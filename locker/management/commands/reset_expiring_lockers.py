# locker/management/commands/update_expired_lockers.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from locker.models import LockerOrder

class Command(BaseCommand):
    help = '대여 종료 시간이 지난 LockerOrder의 상태를 업데이트하고, 관련 Locker를 사용가능 상태로 변경합니다.'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_orders = LockerOrder.objects.filter(locker_status=LockerOrder.Status.INSERVICE)
        
        for order in expired_orders:
            if order.order_end_date < now:
                order.locker_status = LockerOrder.Status.OUTSERVICE
                if order.locker:
                    order.locker.is_using = False
                    order.locker.save()
                order.save()
                self.stdout.write(f"LockerOrder {order.pk} 상태를 OUTSERVICE로 업데이트했습니다.")
        
        self.stdout.write("모든 만료된 주문의 상태 업데이트가 완료되었습니다.")
