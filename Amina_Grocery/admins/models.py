from django.db import models

# Create your models here.

class Coupons(models.Model):
    coupon_no=models.CharField(max_length=10)
    discount_percentage=models.IntegerField()
    min_order_price=models.IntegerField()
    status=models.BooleanField(default=True)

    def __str__(self):
        return self.coupon_no
        