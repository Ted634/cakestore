from django import forms
from .models import Profile, Order, Cake
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# 會員資訊表單(會員帳號跟密碼利用 django裡預設的 auth.User)
class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = ['address', 'phone']


# 訂單表單
class OrderForm(forms.ModelForm):
    cake = forms.ModelChoiceField(
        queryset=Cake.objects.all(), empty_label="Select Cake")

    class Meta:
        model = Order
        fields = ['cake', 'quantity']
