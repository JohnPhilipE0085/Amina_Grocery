from django.shortcuts import render, redirect,get_object_or_404
from .models import Product,categories
from .forms import ProductForm
from django.contrib import messages
from admins.decorators import staff_login_required
import base64
from django.core.files.base import ContentFile

@staff_login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)

            for i in range(1, 4):  # image1, image2, image3
                cropped_data = request.POST.get(f"cropped_image{i}")
                if cropped_data:
                    format, imgstr = cropped_data.split(';base64,')
                    ext = format.split('/')[-1]
                    img_file = ContentFile(base64.b64decode(imgstr), name=f'cropped_image{i}.{ext}')
                    setattr(product, f'image{i}', img_file)

            product.save()
            request.session['product_variant_id'] = product.id

            if product.variant:
                return redirect('add_variants')
            return redirect('admin_products')   
    else:
        form = ProductForm()
    return render(request, 'admin/products/add_product.html', {'form': form})

import re
from django.db.models import Max
def add_variants(request):
    product_id=request.session.get('product_variant_id')
    product_details=Product.objects.get(id=product_id)
    variant_no=Product.objects.aggregate(Max('variant_id'))['variant_id__max'] 
    variant_id=int(variant_no)+1
    product_details.variant_id=variant_id
    product_details.save()
    if request.method=="POST":
        names = request.POST.getlist('variant_name[]')
        prices = request.POST.getlist('variant_price[]')
        offer_prices = request.POST.getlist('variant_offer_price[]')
        
        for name, price, offer in zip(names, prices, offer_prices):
            variant_name=f"{product_details.name}({name})"
            variant_price=int(price)
            variant_offer_price=int(offer)
            variant_quantity=int(''.join(re.findall(r'\d+', variant_name)))/1000
            Product.objects.create(name=variant_name,description=product_details.description,price=variant_price,
                                   offer_price=variant_offer_price,image1=product_details.image1,image2=product_details.image2,
                                   image3=product_details.image3,variant=True,stock=product_details.stock,is_in_stock=product_details.is_in_stock,
                                   variant_quantity=variant_quantity,variant_id=variant_id,category=product_details.category,)

        return redirect('admin_products')
    return render(request,'admin/products/add_variants.html')
    
    
@staff_login_required
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'admin/products/list_products.html', {'products': products})

@staff_login_required
def product(request,product_id):
    request.session['product_id']=product_id
    product = get_object_or_404(Product, id=product_id)
    return render(request,'admin/products/product.html',{"products":product})

@staff_login_required
def edit_product_option(request,product_id):
    product=Product.objects.get(id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)  
        if form.is_valid():
            form.save()
            return redirect('admin_products')  
    else:
        form = ProductForm(instance=product) 
    return render(request,'admin/products/edit_product.html',{"form":form})

@staff_login_required
def edit_product(request):
    if request.method=="POST":
        name=request.POST.get('name')
        description=request.POST.get('description')
        price=request.POST.get('price')
        offer_price=request.POST.get('offer_price')
        category=request.POST.get('category')
        product_id=request.session.get('product_id')
        stock=request.POST.get('stock')

        if price<offer_price:
            messages.error(request,'offer_price is higher than original price')
            return render(request,"admin/products/edit_product.html")
    
        category_instance=categories.objects.get(id=category)

        Product.objects.filter(id=product_id).update(name=name,description=description,price=price,offer_price=offer_price,stock=stock,category=category_instance)
        messages.success(request,'edited product succesffully')
        return redirect('admin_products')
    return render(request, 'admin/products/edit_product.html')

@staff_login_required
def delete_product(request):
    product_id=request.session.get('product_id')
    Product.objects.filter(id=product_id).update(is_in_stock=False)
    messages.success(request,'Deleted the Product Successfully')
    return redirect('admin_products')
    
@staff_login_required
def activate_product(request):
    product_id=request.session.get('product_id')
    Product.objects.filter(id=product_id).update(is_in_stock=True)
    messages.success(request,'activated the Product Successfully')
    return redirect('admin_products')

@staff_login_required
def search_product(request):
    if request.method=="POST":
        search_product=request.POST.get('search_product')
        product=Product.objects.filter(name__icontains=search_product)
        
        if product.exists():
            return render(request, 'admin/products/list_products.html', {'products': product})

    messages.error(request,'no product found')
    return redirect('admin_products')

@staff_login_required
def product_category(request):

    category_names = categories.objects.all()

    if request.method=="POST":
        category=request.POST.get('category','').capitalize()
        
        if categories.objects.filter(name=category).exists():
            messages.error(request,'The provided category is already exists...')
            return redirect('product_category')
        else:
            categories.objects.create(name=category)
            messages.success(request,'Successfully created a new Category...')
            return redirect('product_category')

    return render(request,'admin/products/product_category.html',{"category":category_names})

@staff_login_required
def delete_category(request,category):
    category_id=categories.objects.get(name=category)
    category_filter=Product.objects.filter(category_id=category_id.id,is_in_stock=True)
    if category_filter.exists():
        messages.error(request,'You cannot delete this category because it is associated with some products.')
        return redirect('product_category')
    del_category=categories.objects.get(name=category)
    del_category.is_active=False
    del_category.save()
    messages.success(request,'successfully deleted category')
    return redirect('product_category')

@staff_login_required
def activate_category(request,category):
    act_category=categories.objects.get(name=category)
    act_category.is_active=True
    act_category.save()
    messages.success(request,'successfully activated category')
    return redirect('product_category')

@staff_login_required
def edit_category(request):
    if request.method == "POST":
        category_id = request.POST.get("id")
        new_name = request.POST.get("name")
        categorys=categories.objects.get(id=category_id)
        categorys.name=new_name
        categorys.save()
    return redirect('product_category')
