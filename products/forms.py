from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['variant_id', 'variant_quantity']  # Removed these two fields

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        actual_price = cleaned_data.get("price")
        offer_price = cleaned_data.get("offer_price")
        name = cleaned_data.get('name')
        stock=cleaned_data.get('stock')

        if name:
            cleaned_name = name.strip().capitalize()
            cleaned_data['name'] = cleaned_name

            exists = Product.objects.filter(
                name__iexact=cleaned_name
            ).exclude(pk=self.instance.pk).exists()
            if exists:
                self.add_error('name', "This product already exists.")
        
        if stock:
            if int(stock)<0:
                self.add_error('stock','stock cannot be 0 or less than 0')
            if int(stock)==0:
                self.add_error('stock','stock cannot be 0 or less than 0')

        if actual_price is not None and offer_price is not None:
            if int(offer_price) > int(actual_price):
                self.add_error('offer_price', "Offer price must be less than the actual price.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.category:
            instance.category.is_active = True
            instance.category.save()

        if commit:
            instance.save()
        return instance

