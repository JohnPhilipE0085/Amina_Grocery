import random
from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.models import User
import uuid


def generate_unique_referral_code():
    # Generates a short unique referral code
    return str(uuid.uuid4()).split('-')[0]  # e.g., 'f3c2a1b2'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    first_time_login = models.BooleanField(default=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Set unique referral code only if it doesn't already exist
        if not self.referral_code:
            while True:
                code = generate_unique_referral_code()
                if not UserProfile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)
   
    def __str__(self):
        return self.user.username

class OTPStorage(models.Model):
    email = models.EmailField(unique=True)  # Ensure one OTP per user
    otp = models.CharField(max_length=6, editable=False)  # Auto-generated OTP
    created_at = models.DateTimeField(auto_now_add=True)  # Record when OTP was created
    expires_at = models.DateTimeField()  # Record OTP expiration time

    def generate_new_otp(self):
        """Generate a new OTP that is different from the current one"""
        new_otp = str(random.randint(100000, 999999))
        while new_otp == self.otp:  # Ensure OTP is different
            new_otp = str(random.randint(100000, 999999))
        return new_otp

    def save(self, *args, **kwargs):
        """Automatically generate a new OTP when saving"""
        if not self.otp:  # If OTP is not already set, generate a new one
            self.otp = str(random.randint(100000, 999999))
        else:
            self.otp = self.generate_new_otp()  # Ensure OTP is different
        self.expires_at = now() + timedelta(minutes=5)  # Reset expiration time
        super().save(*args, **kwargs)

    @classmethod
    def create_or_update_otp(cls, email):
        """Ensure OTP is updated or created for a user"""
        otp_entry, created = cls.objects.get_or_create(email=email)
        otp_entry.otp = otp_entry.generate_new_otp()  # Generate a different OTP
        otp_entry.expires_at = now() + timedelta(minutes=5)  # Reset expiration
        otp_entry.save()
        return otp_entry

    def is_expired(self):
        """Check if OTP is expired"""
        return now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email} - {self.otp} (Expires at {self.expires_at})"


class address(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    full_name=models.CharField(max_length=50)
    house_no=models.CharField(max_length=200)
    phone_no=models.CharField(max_length=12)
    pincode=models.IntegerField()
    city=models.CharField(max_length=50)
    place=models.CharField(max_length=50)
    land_mark=models.CharField(max_length=100)
    wallet_amount=models.IntegerField(default=0)

    def __str__(self):
        return self.full_name
    
class wallet_history(models.Model):
    order_id=models.UUIDField()
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    amount=models.IntegerField()
    time=models.DateTimeField(auto_now_add=True)
    reason=models.CharField(max_length=50)

    def __str__(self):
        return f"{self.order_id} - {self.amount} - {self.reason}"    