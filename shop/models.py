from django.db import models
from django.contrib.auth.models import User

# Create your models here.


# 商品資料表
class Cake(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    image = models.ImageField(upload_to='cakes/')
    # 會將指定的圖片上傳到 'cakes/'路徑

    def __str__(self):
        return self.name


# 訂單資料表
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cake = models.ForeignKey(Cake, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=10, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)  # 確認新增的字段

    def __str__(self):
        return f'{self.user.username} - {self.cake.name}'


# 會員資訊資料表
class Profile(models.Model):
    # 使用 django預設的使用者資料表 auth.User
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username
