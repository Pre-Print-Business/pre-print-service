from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
from django.conf import settings
from django.http import Http404
from django.utils.functional import cached_property
from iamport import Iamport
import logging

User = get_user_model()

class PassOrder(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "주문요청"
        FAILED_PAYMENT = "failed_payment", "결제실패"
        PAID = "paid", "결제완료"
        PREPARED_PRODUCT = "prepared_product", "상품준비중"
        SHIPPED = "shipped", "배송중"
        DELIVERED = "delivered", "배송완료"
        CANCELLED = "cancelled", "주문취소"

    pass_order_user = models.ForeignKey(verbose_name='사용자번호', to=User, on_delete=models.CASCADE, null=True, blank=True)
    pass_order_price = models.DecimalField(verbose_name='가격', max_digits=10, decimal_places=2)
    pass_order_pin_number = models.CharField(verbose_name='핀 번호', max_length=16)
    pass_order_color = models.CharField(verbose_name='색상', max_length=2)
    pass_order_date = models.DateTimeField(verbose_name='주문날짜', auto_now_add=True)
    status = models.CharField(
        "진행상태",
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    total_pages = models.IntegerField(verbose_name="총 페이지 수", default=0)
    pass_order_quantity = models.IntegerField(verbose_name="출력 수량", default=1, null=True, blank=True)
    is_takeout = models.BooleanField(verbose_name="테이크아웃 여부", default=False)

    @property
    def name(self) -> str:
        return f"Order {self.pk}"

    def can_pay(self) -> bool:
        return self.status in (self.Status.REQUESTED, self.Status.FAILED_PAYMENT)


class PassOrderFile(models.Model):
    pass_order = models.ForeignKey(PassOrder, on_delete=models.CASCADE)
    pass_order_file = models.FileField(upload_to='pass_order_files/')

class PrintQueue(models.Model):
    created_at = models.DateTimeField(verbose_name='생성 시각', auto_now_add=True, db_index=True)
    pass_order = models.ForeignKey(PassOrder, verbose_name='패스 주문', on_delete=models.CASCADE)
    is_print = models.BooleanField(verbose_name='인쇄 여부', default=False, db_index=True)
    log = models.CharField(verbose_name='로그', max_length=300, null=True, blank=True, db_index=True)
    pass_order_ip = models.CharField(verbose_name='요청 IP', max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Print Queue #{self.id} - Order: {self.pass_order.id} - Printed: {self.is_print}"

    class Meta:
        verbose_name = '인쇄 대기열'
        verbose_name_plural = '인쇄 대기열'


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
    
class PassOrderPayment(AbstractPortonePayment):
    pass_order = models.ForeignKey(PassOrder, on_delete=models.CASCADE, db_constraint=False)

    def update(self, response=None):
        super().update(response)

        if self.is_paid_ok:
            self.pass_order.status = PassOrder.Status.PAID
            self.pass_order.save()
            self.pass_order.passorderpayment_set.exclude(pk=self.pk).delete()

        elif self.pay_status == self.PayStatus.FAILED:
            self.pass_order.status = PassOrder.Status.FAILED_PAYMENT
            self.pass_order.save()

        elif self.pay_status == self.PayStatus.CANCELLED:
            self.pass_order.status = PassOrder.Status.CANCELLED
            self.pass_order.save()

    @classmethod
    def create_by_pass_order(cls, pass_order: PassOrder) -> "PassOrderPayment":
        return cls.objects.create(
            pass_order=pass_order,
            name=pass_order.name,
            desired_amount=pass_order.pass_order_price,
            buyer_name=pass_order.pass_order_user.get_full_name() or pass_order.pass_order_user.username,
            buyer_email=pass_order.pass_order_user.email,
        )