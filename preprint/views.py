import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, OrderFile, OrderPayment
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.timezone import now
from django.utils.timezone import localtime
from datetime import time
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

### 메인페이지, 프린트 설정 페이지, 결제 페이지
def print_main(req):
    return render(req, 'print_main.html')

def guide(req):
    return render(req, 'preprintcloud_guide.html')

### 윈도우 용
# def get_pdf_page_count(pdf_path):
#     cmd = ["C:\\Users\\Owner\\anaconda3\\Library\\bin\\pdfinfo.exe", pdf_path]
#     try:
#         output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
#         for line in output.stdout.decode('utf-8').splitlines():
#             if "Pages:" in line:
#                 return int(line.split(":")[1].strip())
#         return 0
#     except subprocess.CalledProcessError:
#         return 0

### 맥 용
def get_pdf_page_count(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            return doc.page_count
    except Exception as e:
        return 0
    
def get_available_locker_number():
    used_numbers = (
        Order.objects.filter(locker_number__isnull=False)
        .order_by("locker_number")
        .values_list("locker_number", flat=True)
    )

    for i in range(1, 31):
        if i not in used_numbers:
            return i
    return None

def print_detail(req):
    if req.method == "GET":
        if not req.user.is_authenticated:
            return redirect('login')
        else:
            return render(req, "preprint/print_detail.html")
    
    elif req.method == "POST":
        files = req.FILES.getlist('files')
        color = req.POST['color']
        pw = req.POST['pw']
        if not files:
            messages.error(req, "파일을 선택해주세요.")
            return render(req, "preprint/print_detail.html")
        for file in files:
            if not file.name.endswith('.pdf'):
                messages.error(req, "PDF 파일만 업로드 가능합니다.")
                return render(req, "preprint/print_detail.html")

        total_size = sum(file.size for file in files)
        if total_size > 100 * 1024 * 1024:  # 100MB 초과 여부 확인
            messages.error(req, "모든 파일의 크기 합이 100MB를 초과할 수 없습니다.")
            return render(req, "preprint/print_detail.html")

        if not pw or not pw.isdigit() or len(pw) != 4:
            messages.error(req, "비밀번호는 숫자 4자리를 입력해야 합니다.")
            return render(req, "preprint/print_detail.html")

        total_pages = 0
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                for chunk in file.chunks():
                    tmpfile.write(chunk)
                total_pages += get_pdf_page_count(tmpfile.name)

        if color == "C":
            page_price = 200
        else:
            page_price = 50

        order_price = total_pages * page_price
        order = Order.objects.create(order_user=req.user, order_price=order_price, order_pw=pw, order_color=color)
        for file in files:
            OrderFile.objects.create(order=order, file=file)
        return redirect('print_payment_ready', order_id=order.id)
    
def print_payment_ready(req, order_id):
    order = get_object_or_404(Order, id=order_id, order_user=req.user)
    order_files = OrderFile.objects.filter(order=order)
    context = {
        'order': order,
        'files': order_files,
    }
    return render(req, 'preprint/print_payment_ready.html', context)


def print_payment(req):
    orders_to_pay = Order.objects.filter(order_user=req.user, status__in=[Order.Status.REQUESTED, Order.Status.FAILED_PAYMENT]).order_by('-order_date')
    
    if not orders_to_pay.exists():
        messages.error(req, "결제를 할 수 있는 주문이 존재하지 않습니다.")
        return redirect('mypage')

    latest_order = orders_to_pay.first()

    locker_number = get_available_locker_number()
    if locker_number is None:
        messages.error(req, "사물함이 모두 할당되어있습니다.")
        return redirect('print_main')

    latest_order.locker_number = locker_number
    latest_order.save()

    payment = OrderPayment.create_by_order(latest_order)

    check_url = reverse("print_payment_check", args=[latest_order.pk, payment.pk])

    payment_props = {
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.desired_amount,
        "buyer_name": payment.buyer_name,
        "buyer_email": payment.buyer_email,
        "m_redirect_url": req.build_absolute_uri(check_url),
    }

    return render(
        req,
        "preprint/print_payment.html",
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

    order = get_object_or_404(Order, id=order_id, order_user=req.user)
    payment = get_object_or_404(OrderPayment, id=payment_id, order=order)

    if payment.is_paid_ok:
        messages.error(req, "이미 결제된 주문입니다.")
        return redirect('print_payment_list')

    if not order.locker_number:
        locker_number = get_available_locker_number()
        if locker_number is None:
            messages.error(req, "사물함이 모두 할당되어있습니다.")
            return redirect('print_main')
        
        order.locker_number = locker_number
        order.save()

    check_url = reverse("print_payment_check", args=[order.pk, payment.pk])

    payment_props = {
        "merchant_uid": str(payment.uid),
        "name": payment.name,
        "amount": payment.desired_amount,
        "buyer_name": payment.buyer_name,
        "buyer_email": payment.buyer_email,
        "m_redirect_url": req.build_absolute_uri(check_url),
    }

    return render(
        req,
        "preprint/print_payment.html",
        {
            "portone_shop_id": settings.PORTONE_SHOP_ID,
            "payment_props": payment_props,
            "next_url": check_url,
        },
    )



@login_required
def print_payment_check(req, order_pk, payment_pk):
    payment = get_object_or_404(OrderPayment, pk=payment_pk, order__pk=order_pk)
    payment.update()

    if not payment.is_paid_ok:
        payment.order.locker_number = None
        payment.order.save()

    return redirect("print_payment_detail", order_pk=order_pk)

@login_required
def print_payment_detail(req, order_pk):
    order = get_object_or_404(Order, pk=order_pk, order_user=req.user)
    order_files = OrderFile.objects.filter(order=order)
    payment = OrderPayment.objects.filter(order=order).first()
    context = {
        'order': order,
        'files': order_files,
        'payment': payment,
    }
    return render(req, 'preprint/print_payment_detail.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, order_user=request.user)
    
    current_time = localtime().time()
    
    # 취소 불가능 시간대 설정 (01:00 ~ 09:00)
    cancel_start_time = time(1, 0)
    cancel_end_time = time(9, 0)

    # 현재 시간이 취소 불가능 시간대에 해당하면
    if cancel_start_time <= current_time < cancel_end_time:
        messages.error(request, "현재 시간에는 주문 취소가 불가능합니다. 주문 취소는 01시부터 09시 사이에는 불가능합니다.")
        return redirect('print_payment_list')

    # 주문이 이미 취소된 상태인지 확인
    if order.status == Order.Status.CANCELLED:
        messages.error(request, "이 주문은 이미 취소되었습니다.")
        return redirect('print_payment_list')

    # 주문이 취소 가능한 상태인지 확인
    if order.status in [Order.Status.PAID, Order.Status.PREPARED_PRODUCT, Order.Status.SHIPPED, Order.Status.DELIVERED]:
        payment = OrderPayment.objects.filter(order=order).first()
        if payment and payment.pay_status == OrderPayment.PayStatus.PAID:
            try:
                payment.cancel(reason="User requested cancellation")
            except Exception as e:
                messages.error(request, f"결제 취소 중 오류가 발생했습니다: {str(e)}")
                return redirect('print_payment_list')

    # 주문 상태를 취소로 업데이트
    order.status = Order.Status.CANCELLED
    order.locker_number = None
    order.save()
    messages.success(request, "주문이 취소되었습니다.")
    return redirect('print_payment_list')


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

    orders = Order.objects.filter(order_user=req.user).order_by('-order_date')
    orders_with_files = []
    
    for order in orders:
        order_files = OrderFile.objects.filter(order=order)
        payment = OrderPayment.objects.filter(order=order).first()
        orders_with_files.append({
            'order': order,
            'files': order_files,
            'payment': payment,
        })
    
    context = {
        'orders_with_files': orders_with_files,
        'orders_count': orders.count(),
    }
    return render(req, 'preprint/payment_list.html', context)


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

    payment = get_object_or_404(OrderPayment, uid=merchant_uid)
    payment.update()

    return HttpResponse("ok")