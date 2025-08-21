from django.db import models
from django.contrib.auth.models import User
from products.models import Product
import uuid
from admins.models import Coupons
from user.models import address

# Create your models here.

class WishList(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    added_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"


class Orders(models.Model):
    order_id= models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  
    user= models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.IntegerField(default=0)
    price=models.IntegerField(default=0)
    total_price=models.IntegerField(default=0)
    discount_price=models.IntegerField(default=0)
    address = models.ForeignKey(address, on_delete=models.SET_NULL, null=True, blank=True)
    coupon=models.ForeignKey(Coupons,null=True,blank=True,on_delete=models.PROTECT)
    payment_option=models.CharField(max_length=25,choices=[('cod','cod'),('wallet_pay','wallet_pay'),('razorpay','razorpay')])
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    cart_id=models.IntegerField(default=0)
    delivery_status=models.CharField(max_length=20,choices=[('Confirmed','Confirmed'),('Shipped','Shipped'),('Delivered','Delivered'),('Cancelled','Cancelled'),('Returned','Returned')],default='Confirmed')
    
    reviewed = models.BooleanField(default=False)
    review = models.TextField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.order_id} for {self.user.username}"

    def save(self, *args, **kwargs):
        self.total_price = self.price - self.discount_price
        super().save(*args, **kwargs)


class ReturnProduct(models.Model):
    order=models.OneToOneField(Orders,on_delete=models.CASCADE)
    reason=models.TextField()
    status = models.CharField(max_length=20, choices=[('Requested', 'Requested'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Refunded', 'Refunded')], default='Requested')
    created_at=models.DateTimeField(auto_now_add=True)

