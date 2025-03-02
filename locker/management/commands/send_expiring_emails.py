# locker/management/commands/send_expiring_emails.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from locker.models import LockerOrder
import smtplib
from email.message import EmailMessage
from django.conf import settings

# Gmail 앱 비밀번호와 발신자 이메일 (실제 이메일 주소로 수정하세요)
APP_PASSWORD = settings.APP_PASSWORD
SENDER_EMAIL = "preprint.official@gmail.com"  # 예: your_email@gmail.com

class Command(BaseCommand):
    help = "서비스 만료 임박 주문 건에 대해 이메일 알림을 발송합니다."

    def handle(self, *args, **options):
        now = timezone.localtime()
        # locker_status가 INSERVICE인 주문들만 필터링
        orders = LockerOrder.objects.filter(locker_status=LockerOrder.Status.INSERVICE)
        emails_sent = 0

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
        except Exception as e:
            self.stderr.write("SMTP 연결 실패: " + str(e))
            return

        for order in orders:
            remaining_time = order.order_end_date - now
            total_seconds = remaining_time.total_seconds()
            # 남은 시간이 3일 이하이면서 아직 만료되지 않은 경우
            if 0 < total_seconds <= 3 * 24 * 3600:
                # 남은 시간을 일, 시간, 분, 초로 분해
                days = remaining_time.days
                hours, rem = divmod(remaining_time.seconds, 3600)
                minutes, seconds = divmod(rem, 60)
                
                subject = "사물함 서비스 만료 안내"
                message_body = (
                    f"{order.order_user.username}님, 대여하신 {order.locker.locker_number}번 사물함 사용기간이 "
                    f"{days}일 {hours}시간 {minutes}분 {seconds}초 남았습니다. "
                    f"사물함 서비스 이용 종료 날짜는 {order.order_end_date.strftime('%Y-%m-%d %H:%M:%S')}입니다."
                )
                msg = EmailMessage()
                msg.set_content(message_body)
                msg['Subject'] = subject
                msg['From'] = SENDER_EMAIL
                msg['To'] = order.order_user.email

                try:
                    server.send_message(msg)
                    emails_sent += 1
                    self.stdout.write(f"Email sent to {order.order_user.email}")
                except Exception as e:
                    self.stderr.write(f"Failed to send email to {order.order_user.email}: {e}")

        server.quit()
        self.stdout.write(f"총 발송 이메일 수: {emails_sent}")
