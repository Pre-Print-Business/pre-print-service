

from django.shortcuts import render, redirect
from .models import Order, OrderFile
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# Create your views here.

def print_main(req):
    # if req.method == "GET":
    #     return render(req, 'print_main.html')
    # elif req.method == "POST":
    #     return render(req, "print_detail.html")
    print(req.method)
    return render(req, 'print_main.html')

def print_detail(req):
    if req.method == "GET":
        return render(req, "print_detail.html")
    elif req.method == "POST":
        if req.user.is_authenticated:
            files = req.FILES.getlist('files')
            color = req.POST['color']
            pw = req.POST['pw']

            # Check if files and password are provided
            if not files or not pw:
                messages.error(req, "정보를 채워주세요")
                return render(req, "print_detail.html")

            order = Order.objects.create(order_user=req.user, order_price=200, order_pw=pw, order_color=color)

            for file in files:
                OrderFile.objects.create(order=order, file=file)
            
            return redirect('payment')
        else:
            return redirect('main')

def print_payment(req):
    if req.user.is_authenticated:
        user_orders = Order.objects.filter(order_user=req.user)
        files = []
        for order in user_orders:
            order_files = OrderFile.objects.filter(order=order)
            for order_file in order_files:
                files.append(order_file)
        context = {
            'files': files,
        }
        return render(req, 'print_payment.html', context)
    elif req.method == "POST":
        # print(req.POST['color'])
        return render(req, 'print_payment.html')

