

from django.shortcuts import render, redirect
from .models import Order, OrderFile
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import PyPDF2
from django.core.files.uploadedfile import InMemoryUploadedFile


### 메인페이지, 프린트 설정 페이지, 결제 페이지
def print_main(req):
    return render(req, 'print_main.html')

def print_detail(req):
    if req.method == "GET":
        if not req.user.is_authenticated:
            return redirect('accounts:login')
        else:
            return render(req, "print_detail.html")
    elif req.method == "POST":
        files = req.FILES.getlist('files')
        color = req.POST['color']
        pw = req.POST['pw']

        if not files or not pw:
            messages.error(req, "비밀번호 4자리를 채워주세요")
            return render(req, "print_detail.html")
        
        # 페이지 계산
        total_pages = 0
        for file in files:
            if isinstance(file, InMemoryUploadedFile):
                pdf = PyPDF2.PdfReader(file)
                total_pages += len(pdf.pages)
        
        order_price = total_pages * 100

        order = Order.objects.create(order_user=req.user, order_price=order_price, order_pw=pw, order_color=color)

        for file in files:
            OrderFile.objects.create(order=order, file=file)
        
        return redirect('payment')

def print_payment(req):
    latest_order = Order.objects.filter(order_user=req.user).order_by('-order_date').first()
    files = []
    if latest_order:
        order_files = OrderFile.objects.filter(order=latest_order)
        for order_file in order_files:
            files.append(order_file)
    context = {
        'files': files,
    }
    return render(req, 'print_payment.html', context)


### 마이페이지 & 결제내역
def print_mypage(req):
    if not req.user.is_authenticated:
        return redirect('accounts:login')
    context = {
        'user': req.user
    }
    return render(req, 'preprint/mypage.html', context)

def print_payment_detail(req):
    if not req.user.is_authenticated:
        return redirect('accounts:login')

    orders = Order.objects.filter(order_user=req.user).order_by('-order_date')
    orders_with_files = []
    
    for order in orders:
        order_files = OrderFile.objects.filter(order=order)
        orders_with_files.append({
            'order': order,
            'files': order_files,
        })
    
    context = {
        'orders_with_files': orders_with_files,
        'orders_count': orders.count(),
    }

    return render(req, 'preprint/payment_detail.html', context)


