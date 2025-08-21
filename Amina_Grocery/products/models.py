from django.db import models
from PIL import Image

class categories(models.Model):
    name=models.CharField(max_length=50,unique=True)
    is_active=models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image1 = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.DecimalField(max_digits=6, decimal_places=3, default=1)
    variant=models.BooleanField(default=False)
    variant_id=models.IntegerField(default=0)
    variant_quantity=models.DecimalField(max_digits=6, decimal_places=3, default=1)
    is_in_stock = models.BooleanField(default=True)
    category = models.ForeignKey('categories', on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    
    # Offer
    offer_point = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        self.is_in_stock = self.stock > 0
        
        super().save(*args, **kwargs)  

       
        target_size = (500, 500)

        def crop_image(image_field):
            if image_field:
                image_path = image_field.path
                try:
                    img = Image.open(image_path)
                    img = img.convert("RGB")  # Ensure it's in RGB mode
                    img = img.resize(target_size, Image.LANCZOS)  # Resize with high quality
                    img.save(image_path, quality=90)  # Save back with reduced size
                except Exception as e:
                    print(f"Error processing image: {e}")

        # Crop all images if they exist
        crop_image(self.image1)
        crop_image(self.image2)
        crop_image(self.image3)

    def __str__(self):
        return self.name
    
    
class Category_offers(models.Model):
    category = models.OneToOneField(categories, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    backup_prices = models.JSONField(default=dict, blank=True)  # ✅ Store original offer_price per product

    def __str__(self):
        return f"{self.category.name} - {self.discount_percentage}%"