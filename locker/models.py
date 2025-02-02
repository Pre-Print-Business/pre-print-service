from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
from django.conf import settings
from django.http import Http404
from django.utils.functional import cached_property
from iamport import Iamport

User = get_user_model()

class Locker(models.Model):
    locker_number = models.IntegerField(unique=True)
    is_using = models.BooleanField(default=False)

    def __str__(self):
        return f"Locker {self.locker_number} - {'In Use' if self.is_using else 'Available'}"

class LockerOrder(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "주문요청"
        FAILED_PAYMENT = "failed_payment", "결제실패"
        PAID = "paid", "결제완료"
        PREPARED_PRODUCT = "prepared_product", "상품준비중"
        SHIPPED = "shipped", "배송중"
        DELIVERED = "delivered", "배송완료"
        CANCELLED = "cancelled", "주문취소"
    order_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="유저")
    locker = models.ForeignKey(Locker, on_delete=models.CASCADE, verbose_name="락커", null=True, blank=True)
    order_price = models.DecimalField(verbose_name="가격", max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(verbose_name='주문날짜', auto_now_add=True)
    order_start_date = models.DateTimeField(verbose_name="대여 시작일")
    order_end_date = models.DateTimeField(verbose_name="대여 종료일")
    rental_period = models.IntegerField(verbose_name="대여 기간(일 단위)")
    status = models.CharField(
        "진행상태",
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )

    @property
    def name(self) -> str:
        return f"Locker Order {self.pk}"

    def can_pay(self) -> bool:
        return self.status in (self.Status.REQUESTED, self.Status.FAILED_PAYMENT)

class AbstractPortonePayment(models.Model):
    class PayMethod(models.TextChoices):
        CARD = "card", "신용카드"
    class PayStatus(models.TextChoices):
        READY = "ready", "결제 준비"
        PAID = "paid", "결제 완료"
        CANCELLED = "cancelled", "결제 취소"
        FAILED = "failed", "결제 실패"

    meta = models.JSONField(
        "포트원 결제내역", 
        default=dict, 
        editable=False
    )
    uid = models.UUIDField(
        "쇼핑몰 결제식별자", 
        default=uuid4, 
        editable=False
    )
    name = models.CharField(
        "결제명", 
        max_length=200
    )
    desired_amount = models.PositiveIntegerField(
        "결제금액", 
        editable=False
    )
    buyer_name = models.CharField(
        "구매자 이름", 
        max_length=100, 
        editable=False
    )
    buyer_email = models.EmailField(
        "구매자 이메일", 
        editable=False
    )
    pay_method = models.CharField(
        "결제수단", 
        max_length=20, 
        choices=PayMethod.choices, 
        default=PayMethod.CARD
    )
    pay_status = models.CharField(
        "결제상태", 
        max_length=20, 
        choices=PayStatus.choices, 
        default=PayStatus.READY
    )
    is_paid_ok = models.BooleanField(
        "결제성공 여부", 
        default=False, 
        db_index=True, 
        editable=False
    )

    @property
    def merchant_uid(self) -> str:
        return str(self.uid).replace("-", "")

    @cached_property
    def api(self):
        return Iamport(
            imp_key=settings.PORTONE_API_KEY, 
            imp_secret=settings.PORTONE_API_SECRET
        )

    def update(self, response=None):
        if response is None:
            try:
                self.meta = self.api.find(merchant_uid=self.merchant_uid)
            except (Iamport.ResponseError, Iamport.HttpError) as e:
                raise Http404("포트원에서 결제내역을 찾을 수 없습니다.")
        else:
            self.meta = response

        self.pay_status = self.meta["status"]
        self.is_paid_ok = self.api.is_paid(self.desired_amount, response=self.meta)
        self.save()

    def cancel(self, reason=""):
        try:
            response = self.api.cancel(reason, merchant_uid=self.merchant_uid)
            self.update(response)
        except Iamport.ResponseError:
            self.update()

    class Meta:
        abstract = True
    
class LockerOrderPayment(AbstractPortonePayment):
    locker_order = models.ForeignKey(LockerOrder, on_delete=models.CASCADE, db_constraint=False)

    def update(self, response=None):
        super().update(response)

        if self.is_paid_ok:
            self.locker_order.status = LockerOrder.Status.PAID
            self.locker_order.save()
            self.locker_order.lockerorderpayment_set.exclude(pk=self.pk).delete()

        elif self.pay_status == self.PayStatus.FAILED:
            self.locker_order.status = LockerOrder.Status.FAILED_PAYMENT
            self.locker_order.save()

        elif self.pay_status == self.PayStatus.CANCELLED:
            self.locker_order.status = LockerOrder.Status.CANCELLED
            self.locker_order.save()

    @classmethod
    def create_by_locker_order(cls, locker_order: LockerOrder) -> "LockerOrderPayment":
        return cls.objects.create(
            locker_order=locker_order,
            name=locker_order.name,
            desired_amount=locker_order.order_price,
            buyer_name=locker_order.order_user.get_full_name() or locker_order.order_user.username,
            buyer_email=locker_order.order_user.email,
        )
