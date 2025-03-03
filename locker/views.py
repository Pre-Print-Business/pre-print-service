import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import LockerOrderPayment, LockerOrder, Locker
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.timezone import now
from django.utils.timezone import localtime
from datetime import datetime, timedelta
from datetime import time
from datetime import timedelta
from django.utils import timezone
# 이건 PyMuPDF
import fitz
# 이건 Poppler-pdfinfo
import subprocess
import tempfile
import os
import PyPDF2
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
import re


def locker_main(req):
    return render(req, 'locker/locker_main.html')

### 메인페이지, 프린트 설정 페이지, 결제 페이지
def print_main(req):
    return render(req, 'print_main.html')

@login_required
def print_detail(req):
    if req.method == "GET":
        if not req.user.is_authenticated:
            return redirect('login')

        lockers = Locker.objects.all().order_by('locker_number')
        return render(req, "locker/print_detail.html", {"lockers": lockers})

    if req.method == "POST":
        locker_id = req.POST.get("locker_id")
        locker_pw = req.POST.get("locker_pw", "").strip()
        plan = req.POST.get("plan")

        # 사물함 비밀번호 유효성 검사: 4자리 숫자여야 함
        if not re.fullmatch(r'\d{4}', locker_pw):
            messages.error(req, "사물함 비밀번호는 반드시 4자리 숫자로 입력해 주세요.")
            lockers = Locker.objects.all().order_by('locker_number')
            return render(req, "locker/print_detail.html", {"lockers": lockers})

        locker = get_object_or_404(Locker, id=locker_id)
        if locker.is_using:
            messages.error(req, "이미 사용 중인 사물함입니다. 다른 사물함을 선택해주세요.")
            lockers = Locker.objects.all().order_by('locker_number')
            return render(req, "locker/print_detail.html", {"lockers": lockers})

        # 고정 서비스 시작일 (03.05) 설정
        fixed_start_date = datetime(2025, 3, 5)
        if plan == "semester":
            fixed_end_date = datetime(2025, 6, 20)
            rental_period = 107
            base_price = 18000
        elif plan == "long":
            fixed_end_date = datetime(2025, 8, 31)
            rental_period = 179
            base_price = 30000
        else:
            messages.error(req, "유효한 이용권을 선택해 주세요.")
            lockers = Locker.objects.all().order_by('locker_number')
            return render(req, "locker/print_detail.html", {"lockers": lockers})

        # 테스트를 위해 current_time을 2025-03-20으로 고정
        # current_time = datetime(2025, 3, 5)
        current_time = datetime.now()
        # 결제시간 기준으로 서비스 시작일 산정
        if current_time.date() < fixed_start_date.date():
            effective_start = fixed_start_date.date()
        else:
            effective_start = current_time.date() + timedelta(days=1)

        # 할인: (결제일 다음날 - 03.05) 일수 × 170원
        discount_days = (effective_start - fixed_start_date.date()).days if effective_start > fixed_start_date.date() else 0
        discount_amount = discount_days * 170
        final_price = base_price - discount_amount

        order = LockerOrder.objects.create(
            order_user=req.user,
            locker=locker,
            order_price=final_price,
            order_start_date=fixed_start_date,
            order_end_date=fixed_end_date,
            rental_period=rental_period,
            locker_pw=locker_pw
        )
        # 필요 시, locker 상태 변경 등의 추가 처리

        return redirect("locker:print_payment_ready", order_id=order.id)
    
def print_payment_ready(req, order_id):
    order = get_object_or_404(LockerOrder, id=order_id, order_user=req.user)
    context = {
        'order': order,
    }
    return render(req, 'locker/print_payment_ready.html', context)


def print_payment(req):
    orders_to_pay = LockerOrder.objects.filter(order_user=req.user, status__in=[LockerOrder.Status.REQUESTED, LockerOrder.Status.FAILED_PAYMENT]).order_by('-order_date')

    if not orders_to_pay.exists():
        messages.error(req, "결제를 할 수 있는 주문이 존재하지 않습니다.")
        return redirect('mypage')

    latest_order = orders_to_pay.first()

    if latest_order.locker.is_using == False:
        latest_order.locker.is_using = True
        latest_order.locker.save()
    else:
        messages.error(req, "다른 유저가 결제 진행중에 있거나 이미 사용중인 사물함입니다. 이후에 다시 시도해주세요.")
        return redirect('locker:print_detail')

    payment = LockerOrderPayment.create_by_locker_order(latest_order)

    check_url = reverse("locker:print_payment_check", args=[latest_order.pk, payment.pk])

    payment_props = {
        "pg": "smartro_v2.imp000112m",
        "pay_method": "card",
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.desired_amount,
        "buyer_email": payment.buyer_email,
        "buyer_name": payment.buyer_name,
        "buyer_tel": req.user.phone,
        # "buyer_addr": "서울특별시",
        # "buyer_postcode": "123",
        "m_redirect_url": req.build_absolute_uri(check_url),
        "period": {
            "from": latest_order.order_start_date.strftime("%Y%m%d"),
            "to": latest_order.order_end_date.strftime("%Y%m%d")
        }
    }

    return render(
        req,
        "locker/print_payment.html",
        {
            "portone_shop_id": settings.PORTONE_SHOP_ID,
            "payment_props": payment_props,
            "next_url": check_url,
        },
    )

@login_required
@require_POST
def retry_payment(req):
    order_id = req.POST.get('order_id')
    payment_id = req.POST.get('payment_id')

    # 주문 ID로 직접 가져오기 (FAILED_PAYMENT 상태 검사 제거)
    order = get_object_or_404(LockerOrder, id=order_id, order_user=req.user)

    if order.locker.is_using == False:
        order.locker.is_using = True
        order.locker.save()
    else:
        messages.error(req, "다른 유저가 결제 진행중에 있거나 이미 사용중인 사물함입니다. 이후에 다시 시도해주세요.")
        return redirect('locker:print_detail')

    # 기존 결제 정보가 없으면 새로운 결제 생성
    if not payment_id or payment_id == '':
        payment = LockerOrderPayment.create_by_locker_order(order)
    else:
        payment = get_object_or_404(LockerOrderPayment, id=payment_id, locker_order=order)

    # 이미 결제된 경우 재결제 방지
    if payment.is_paid_ok:
        messages.error(req, "이미 결제된 주문입니다.")
        return redirect('locker:print_payment_list')

    # 결제하기전 다시 할당 해주기
    order.locker.is_using = True
    order.locker.save()

    # 결제 확인 URL 생성
    check_url = reverse("locker:print_payment_check", args=[order.pk, payment.pk])

    # 포트원 결제 요청 데이터 생성
    payment_props = {
        "pg": "smartro_v2.imp000112m",
        "pay_method": "card",
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.desired_amount,
        "buyer_email": payment.buyer_email,
        "buyer_name": payment.buyer_name,
        "buyer_tel": req.user.phone,
        "m_redirect_url": req.build_absolute_uri(check_url),
        "period": {
            "from": order.order_start_date.strftime("%Y%m%d"),
            "to": order.order_end_date.strftime("%Y%m%d")
        }
    }

    # 결제 페이지로 이동
    return render(
        req,
        "locker/print_payment.html",
        {
            "portone_shop_id": settings.PORTONE_SHOP_ID,
            "payment_props": payment_props,
            "next_url": check_url,
        },
    )

@login_required
def print_payment_check(req, order_pk, payment_pk):
    payment = get_object_or_404(LockerOrderPayment, pk=payment_pk, locker_order__pk=order_pk)
    payment.update()

    if not payment.is_paid_ok:
        print("geag: 실패함 " + str(payment.locker_order.locker.is_using))
        payment.locker_order.locker.is_using = False
        payment.locker_order.locker.save()
    else:
        payment.locker_order.locker_status = payment.locker_order.LockerStatus.INSERVICE
        payment.locker_order.save()
    return redirect("locker:print_payment_detail", order_pk=order_pk)


@login_required
def print_payment_detail(req, order_pk):
    order = get_object_or_404(LockerOrder, pk=order_pk, order_user=req.user)
    payment = LockerOrderPayment.objects.filter(locker_order=order).first()
    context = {
        'order': order,
        'payment': payment,
    }
    return render(req, 'locker/print_payment_detail.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(LockerOrder, id=order_id, order_user=request.user)
    
    # 주문이 이미 취소된 상태인지 확인
    if order.status == LockerOrder.Status.CANCELLED:
        messages.error(request, "이 주문은 이미 취소되었습니다.")
        return redirect('locker:print_payment_list')

    # 주문이 취소 가능한 상태인지 확인
    if order.status in [LockerOrder.Status.PAID, LockerOrder.Status.PREPARED_PRODUCT, LockerOrder.Status.SHIPPED, LockerOrder.Status.DELIVERED]:
        payment = LockerOrderPayment.objects.filter(locker_order=order).first()
        if payment and payment.pay_status == LockerOrderPayment.PayStatus.PAID:
            try:
                payment.cancel(reason="User requested cancellation")
            except Exception as e:
                messages.error(request, f"결제 취소 중 오류가 발생했습니다: {str(e)}")
                return redirect('locker:print_payment_list')

    # 주문 상태를 취소로 업데이트
    order.status = LockerOrder.Status.CANCELLED
    order.locker.is_using = False
    order.save()
    order.locker.save()
    messages.success(request, "주문이 취소되었습니다.")
    return redirect('locker:print_payment_list')

@login_required
def delete_order(request, order_pk):
    order = get_object_or_404(LockerOrder, pk=order_pk, order_user=request.user)
    order.delete()
    messages.success(request, "주문이 삭제되었습니다.")
    return redirect('locker:print_payment_list')

### 마이페이지 & 결제내역
def print_mypage(req):
    if not req.user.is_authenticated:
        return redirect('login')
    context = {
        'user': req.user
    }
    return render(req, 'preprint/mypage.html', context)

@login_required
def print_payment_list(req):
    if not req.user.is_authenticated:
        return redirect('login')
    now = timezone.now()

    active_orders = LockerOrder.objects.filter(order_user=req.user).order_by('-order_date')
    orders_with_files = []

    # Order 처리
    for order in active_orders:
        print(order.order_end_date.strftime('%Y-%m-%d %H:%M:%S'))
        # 주문 상태가 결제완료(PAID) 또는 결제실패(FAILED_PAYMENT)가 아니면
        if order.status not in [LockerOrder.Status.PAID, LockerOrder.Status.FAILED_PAYMENT]:
            continue
        # 결제완료가 아닌 상태에서 주문 시간이 3시간이 지난 경우 삭제
        if order.status != LockerOrder.Status.PAID and now - order.order_date > timedelta(hours=3):
            order.delete()
            continue
        payment = LockerOrderPayment.objects.filter(locker_order=order).first()
        
        # 남은 시간을 정확히 계산 (분까지)
        remaining_delta = order.order_end_date - now
        if remaining_delta.total_seconds() <= 0:
            remaining_str = "0분"
        else:
            days = remaining_delta.days
            hours, rem = divmod(remaining_delta.seconds, 3600)
            minutes, _ = divmod(rem, 60)
            if days > 0:
                remaining_str = f"{days}일 {hours}시간 {minutes}분"
            else:
                remaining_str = f"{hours}시간 {minutes}분"
        
        orders_with_files.append({
            'order': order,
            'payment': payment,
            'remaining_time': remaining_str,
        })
    context = {
        'orders_with_files': orders_with_files,
        'orders_count': len(orders_with_files),
    }
    return render(req, 'locker/payment_list.html', context)

@require_POST
@csrf_exempt
def portone_webhook(request):
    if request.META["CONTENT_TYPE"] == "application/json":
        payload = json.loads(request.body)
        merchant_uid = payload.get("merchant_uid")
    else:
        merchant_uid = request.POST.get("merchant_uid")

    if not merchant_uid:
        return HttpResponse("merchant_uid 인자가 누락되었습니다.", status=400)
    elif merchant_uid == "merchant_1234567890":
        return HttpResponse("test ok")

    payment = get_object_or_404(LockerOrderPayment, uid=merchant_uid)
    payment.update()

    return HttpResponse("ok")