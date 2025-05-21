import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import PassOrder, PassOrderFile, PassOrderPayment, PrintQueue
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
import random

# Create your views here.
def passorder_main(req):
    return render(req, 'passorder/passorder_main.html')


# 상수 정의
MAX_SERVICE_PAGES = 500
MAX_PAGES_PER_REQUEST = 300

# 핀 번호 확인 및 프린트 페이지로 이동
def passorder_pin_check(req):
    if req.method == "GET":
        return render(req, "passorder/passorder_pin_check.html")

    if req.method == "POST":
        pin_number = req.POST.get("pin_number")

        order = PassOrder.objects.filter(pass_order_pin_number=pin_number).first()

        if not order:
            messages.error(req, "해당 핀 번호로 등록된 주문이 없습니다.")
            return render(req, "passorder/passorder_pin_check.html")

        if order.status != 'paid':
            messages.error(req, "결제가 완료되지 않은 주문건은 출력할 수 없습니다.")
            return render(req, "passorder/passorder_pin_check.html")

        if order.is_takeout:
            messages.error(req, "이미 패스오더 프린트를 진행한 주문 핀 번호입니다.")
            return render(req, "passorder/passorder_pin_check.html")

        # 클라이언트 IP 주소 확인
        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip
        
        client_ip = get_client_ip(req)
        
        # 허용된 IP인지 확인 -> 본관에서 데스크탑을 통해서만 가능해야함
        if client_ip != "220.66.17.71":
            messages.error(req, "명지대학교 본관 1층 데스크탑에서만 preprint출력이 가능합니다. 본관 1층 데스크탑에서 시도해주세요.")
            return render(req, "passorder/passorder_pin_check.html")

        files = PassOrderFile.objects.filter(pass_order=order)

        return render(req, "passorder/passorder_printing.html", {"order": order, "files": files})


@csrf_exempt
def passorder_printing(req):
    if req.method == "POST":
        order_id = req.POST.get("order_id")

        pass_order = get_object_or_404(PassOrder, id=order_id)
        pass_order_files = PassOrderFile.objects.filter(pass_order=pass_order)

        # is_takeout을 True로 변경 후 저장
        pass_order.is_takeout = True
        pass_order.save()
        
        # PrintQueue 생성
        PrintQueue.objects.create(
            pass_order=pass_order,
        )

        messages.success(req, f"오더 {order_id}가 성공적으로 출력되었습니다.")

        context = {
            'pass_order': pass_order,
            'files': pass_order_files,
        }
        return render(req, 'passorder/printing_info.html', context)


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

def generate_unique_pin():
    while True:
        pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        if not PassOrder.objects.filter(pass_order_pin_number=pin).exists():
            return pin

def print_detail(req):
    if req.method == "GET":
        if not req.user.is_authenticated:
            return redirect('login')
        
        return render(req, "passorder/print_detail.html")
    elif req.method == "POST":
        files = req.FILES.getlist('files')
        color = req.POST['color']
        # pw = req.POST['pw']
        if not files:
            messages.error(req, "파일을 선택해주세요.")
            return render(req, "passorder/print_detail.html")
        for file in files:
            if not file.name.endswith('.pdf'):
                messages.error(req, "PDF 파일만 업로드 가능합니다.")
                return render(req, "passorder/print_detail.html")

        total_size = sum(file.size for file in files)
        if total_size > 200 * 1024 * 1024:
            messages.error(req, "모든 파일의 크기 합이 200MB를 초과할 수 없습니다.")
            return render(req, "passorder/print_detail.html")

        # if not pw or not pw.isdigit() or len(pw) != 16:
        #     messages.error(req, "비밀번호는 숫자 16자리를 입력해야 합니다.")
        #     return render(req, "passorder/print_detail.html")

        pw = generate_unique_pin()

        total_pages = 0
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                for chunk in file.chunks():
                    tmpfile.write(chunk)
                total_pages += get_pdf_page_count(tmpfile.name)
        
        if total_pages == 0:
            messages.error(req, "업로드된 PDF 파일의 페이지 수를 확인할 수 없습니다. 파일이 손상되었거나 잘못된 파일일 수 있습니다. 다시 시도해 주세요.")
            return render(req, "passorder/print_detail.html")

        if total_pages > MAX_PAGES_PER_REQUEST:
            messages.error(req, f"총합 {MAX_PAGES_PER_REQUEST}장 이상의 파일은 신청이 불가합니다.")
            return render(req, "passorder/print_detail.html")

        if color == "C":
            page_price = 300
        else:
            page_price = 75

        order_price = total_pages * page_price

        if order_price < 100:
            order_price = 100

        pass_order_price = total_pages * page_price

        if pass_order_price < 100:
            pass_order_price = 100

        pass_order = PassOrder.objects.create(
            pass_order_user=req.user, 
            pass_order_price=pass_order_price, 
            pass_order_pin_number=pw, 
            pass_order_color=color,
            total_pages=total_pages
        )

        for file in files:
            PassOrderFile.objects.create(pass_order=pass_order, pass_order_file=file)
        return redirect('passorder:print_payment_ready', order_id=pass_order.id)

def print_payment_ready(req, order_id):
    pass_order = get_object_or_404(PassOrder, id=order_id, pass_order_user=req.user)
    pass_order_files = PassOrderFile.objects.filter(pass_order=pass_order)
    context = {
        'pass_order': pass_order,
        'files': pass_order_files,
    }
    return render(req, 'passorder/print_payment_ready.html', context)


def print_payment(req):
    orders_to_pay = PassOrder.objects.filter(pass_order_user=req.user, status__in=[PassOrder.Status.REQUESTED, PassOrder.Status.FAILED_PAYMENT]).order_by('-pass_order_date')
    if not orders_to_pay.exists():
        messages.error(req, "결제를 할 수 있는 주문이 존재하지 않습니다.")
        return redirect('mypage')

    latest_order = orders_to_pay.first()
    payment = PassOrderPayment.create_by_pass_order(latest_order)
    check_url = reverse("passorder:print_payment_check", args=[latest_order.pk, payment.pk])

    now = datetime.now()
    next_day = now + timedelta(days=1)
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
            "from": now.strftime("%Y%m%d"),
            "to": next_day.strftime("%Y%m%d")
        }
    }

    return render(
        req,
        "passorder/print_payment.html",
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
    pass_order = get_object_or_404(PassOrder, id=order_id, pass_order_user=req.user)

    # 기존 결제 정보가 없으면 새로운 결제 생성
    if not payment_id or payment_id == '':
        payment = PassOrderPayment.create_by_pass_order(pass_order)
    else:
        payment = get_object_or_404(PassOrderPayment, id=payment_id, pass_order=pass_order)

    # 이미 결제된 경우 재결제 방지
    if payment.is_paid_ok:
        messages.error(req, "이미 결제된 주문입니다.")
        return redirect('passorder:print_payment_list')

    # 결제 확인 URL 생성
    check_url = reverse("passorder:print_payment_check", args=[pass_order.pk, payment.pk])

    now = datetime.now()
    next_day = now + timedelta(days=1)

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
            "from": now.strftime("%Y%m%d"),
            "to": next_day.strftime("%Y%m%d")
        }
    }

    # 결제 페이지로 이동
    return render(
        req,
        "passorder/print_payment.html",
        {
            "portone_shop_id": settings.PORTONE_SHOP_ID,
            "payment_props": payment_props,
            "next_url": check_url,
        },
    )



@login_required
def print_payment_check(req, order_pk, payment_pk):
    payment = get_object_or_404(PassOrderPayment, pk=payment_pk, pass_order__pk=order_pk)
    payment.update()

    if not payment.is_paid_ok:
        payment.pass_order.save()

    return redirect("passorder:print_payment_detail", order_pk=order_pk)


@login_required
def print_payment_detail(req, order_pk):
    order = get_object_or_404(PassOrder, pk=order_pk, pass_order_user=req.user)
    order_files = PassOrderFile.objects.filter(pass_order=order)
    payment = PassOrderPayment.objects.filter(pass_order=order).first()
    context = {
        'order': order,
        'files': order_files,
        'payment': payment,
    }
    return render(req, 'passorder/print_payment_detail.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(PassOrder, id=order_id, pass_order_user=request.user)

    if order.is_takeout == True:
        messages.error(request, "이미 출력한 주문은 취소할 수 없습니다.")
        return redirect('passorder:print_payment_list')

    # 주문이 이미 취소된 상태인지 확인
    if order.status == PassOrder.Status.CANCELLED:
        messages.error(request, "이 주문은 이미 취소되었습니다.")
        return redirect('passorder:print_payment_list')

    # 주문이 취소 가능한 상태인지 확인
    if order.status in [PassOrder.Status.PAID, PassOrder.Status.PREPARED_PRODUCT, PassOrder.Status.SHIPPED, PassOrder.Status.DELIVERED]:
        payment = PassOrderPayment.objects.filter(pass_order=order).first()
        if payment and payment.pay_status == PassOrderPayment.PayStatus.PAID:
            try:
                payment.cancel(reason="User requested cancellation")
            except Exception as e:
                messages.error(request, f"결제 취소 중 오류가 발생했습니다: {str(e)}")
                return redirect('passorder:print_payment_list')

    # 주문 상태를 취소로 업데이트
    order.status = PassOrder.Status.CANCELLED
    order.save()
    messages.success(request, "주문이 취소되었습니다.")
    return redirect('passorder:print_payment_list')

@login_required
def delete_order(request, order_pk):
    order = get_object_or_404(PassOrder, pk=order_pk, pass_order_user=request.user)
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
    return render(req, 'passorder/mypage.html', context)

@login_required
def print_payment_list(req):
    if not req.user.is_authenticated:
        return redirect('login')

    active_orders = PassOrder.objects.filter(pass_order_user=req.user).order_by('-pass_order_date')
    orders_with_files = []

    # Order 처리
    for order in active_orders:

        order_files = PassOrderFile.objects.filter(pass_order=order)
        payment = PassOrderPayment.objects.filter(pass_order=order).first()
        orders_with_files.append({
            'order': order,
            'files': order_files,
            'payment': payment
        })
    context = {
        'orders_with_files': orders_with_files,
        'orders_count': len(orders_with_files),
    }
    return render(req, 'passorder/payment_list.html', context)

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

    payment = get_object_or_404(PassOrderPayment, uid=merchant_uid)
    payment.update()

    return HttpResponse("ok")