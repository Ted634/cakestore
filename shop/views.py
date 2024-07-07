from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from .models import Cake, Order, Profile
from .forms import ProfileForm, OrderForm
import logging

# Create your views here.
logger = logging.getLogger(__name__)


# 首頁商品呈現
def index(request):
    cakes = Cake.objects.all()
    return render(request, 'shop/index.html', {'cakes': cakes})


# 使用者註冊
def register(request):
    if request.method == 'POST':
        # auth內建的使用者表單 UserCreationForm (要先import)
        form = UserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            # 接收 profile_form的 email資料
            user.email = profile_form.cleaned_data.get('email')
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
        profile_form = ProfileForm()
    return render(request, 'shop/register.html', {'form': form, 'profile_form': profile_form})


# 使用者登出
@login_required
def user_logout(request):
    logout(request)
    return redirect('index')


# 使用者登入
def user_login(request):
    if request.method == 'POST':
        # django auth預設的使用者登入
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})


# 添加訂單頁面
@login_required
def order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            # order.id -> 該筆訂單紀錄的id(Order資料表自動添加)
            return redirect('order_confirmation', order_id=order.id)
    else:
        form = OrderForm()
    return render(request, 'shop/order.html', {'form': form})


# 歷史訂單頁面
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)  # 去 Order資料表找指定 user的資料
    return render(request, 'shop/order_history.html', {'orders': orders})


# 確認訂單頁面
@login_required
def order_confirmation(request, order_id):
    try:
        # 去 Order資料表找指定 user和 status為'Pending'的資料
        orders = Order.objects.filter(user=request.user, status='Pending')
        total_price = sum(order.cake.price *
                          order.quantity for order in orders)  # 訂單總金額
        if request.method == 'POST':
            order_form = OrderForm(request.POST)
            if order_form.is_valid():
                new_order = order_form.save(commit=False)
                new_order.user = request.user
                new_order.status = 'Pending'
                new_order.save()
                return redirect('order_confirmation', order_id=new_order.id)
    except ObjectDoesNotExist:
        logger.error("Order does not exist.")
        return redirect('index')

    # Calculate individual order item total prices
    # 訂單中每個品項的數量與金額
    order_totals = []
    for order in orders:
        order_total = order.cake.price * order.quantity
        order_totals.append({'order': order, 'order_total': order_total})

    return render(request, 'shop/order_confirmation.html', {
        'orders': order_totals,
        'total_price': total_price,
        'order_form': OrderForm(),
        'order_id': order_id
    })


# 訂單確認 (訂單成功 -> 傳送郵件 + 導向到歷史訂單頁面  訂單失敗 -> 導向到首頁)
@login_required
def order_confirm(request, order_id):
    try:
        orders = Order.objects.filter(user=request.user, status='Pending')
        total_price = sum(order.cake.price *
                          order.quantity for order in orders)
        try:
            # Send confirmation email 傳送確認郵件
            send_mail(
                'Order Confirmation',
                f'Thank you for your order, {request.user.username}. You have ordered the following items:\n\n' + '\n'.join(
                    [f'{order.quantity} x {order.cake.name}' for order in orders]) + f'\n\nTotal price: ${total_price:.2f}.',
                'your-email@gmail.com',  # Replace with your actual email address
                [request.user.email],
                fail_silently=False,
            )
            orders.update(status='Confirmed')  # 訂單完成後，更新 status的狀態
            return redirect('order_history')
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    except ObjectDoesNotExist:
        logger.error("Order does not exist.")
    return redirect('index')


# 增加訂單品項的數量
@login_required
def order_increase(request, order_id):
    order = get_object_or_404(
        Order, id=order_id, user=request.user, status='Pending')
    order.quantity += 1
    order.save()
    return redirect('order_confirmation', order_id=order.id)


# 減少訂單品項的數量
@login_required
def order_decrease(request, order_id):
    order = get_object_or_404(
        Order, id=order_id, user=request.user, status='Pending')
    if order.quantity > 1:
        order.quantity -= 1
        order.save()
    return redirect('order_confirmation', order_id=order.id)


# 刪除該項訂單品項
@login_required
def order_delete(request, order_id):
    order = get_object_or_404(
        Order, id=order_id, user=request.user, status='Pending')
    order.delete()
    return redirect('order_confirmation', order_id=order_id)


# 新增訂單品項與數量
@login_required
def add_item_to_order(request, order_id):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.user = request.user
            new_order.status = 'Pending'
            new_order.save()
    return redirect('order_confirmation', order_id=order_id)
