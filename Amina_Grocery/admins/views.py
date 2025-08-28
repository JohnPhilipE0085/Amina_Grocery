from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Coupons
from django.views.decorators.cache import cache_control
from orders.models import Orders,ReturnProduct
from user.models import UserProfile
from django.db.models import Q,Sum
from .decorators import staff_login_required
from products.models import Product

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff:
                login(request, user) 
                request.session['admin_user']=username
                return redirect('admin_home')  
            else:
                messages.error(request, 'You are a user but not an admin.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'admin/admin_login.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@staff_login_required
def admin_home(request):
    total_users=User.objects.count()
    total_orders=Orders.objects.count()
    orders=Orders.objects.filter(delivery_status='Delivered')
    total_price = orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_discount=Product.objects.aggregate(
    total=Sum(F('price') - F('offer_price'))
)['total']
    context={
        'total_users':total_users,
        'total_orders':total_orders,
        'total_price':total_price,
        'total_discount':total_discount
    }
    return render(request, 'admin/admin_home.html',context)
   

@staff_login_required 
def admin_orders(request):
    orders=Orders.objects.filter(Q(delivery_status='Confirmed')|Q(delivery_status='Shipped'))
    context={
        "orders":orders,
    }
    return render(request,'admin/admin_orders.html',context)

from products.models import categories
from django.db.models import Value,DecimalField,F
from django.db.models.functions import Coalesce
@staff_login_required
def best_selling(request,product):
    if product=="Product":
        top_products = Product.objects.annotate(
        total_sold=Coalesce(
        Sum('orders__quantity'),
        Value(0),
        output_field=DecimalField()
    )).order_by('-total_sold')[:10]
        context={'product':top_products}
    else:
        top_categories = categories.objects.annotate(
    total_sold=Coalesce(
        Sum('products__orders__quantity'),
        Value(0),
        output_field=DecimalField()
    )
).order_by('-total_sold')[:10]
        context={'product':top_categories}
    return render(request,'admin/best_selling.html',context)



@staff_login_required 
def order_status_update(request,order_id,status):
    if status == 'Delivered':
        order=Orders.objects.get(order_id=order_id)
        order.delivery_status='Delivered'
        order.save()
        messages.success(request,'Order delivered successfully')
        return redirect(admin_orders)
    else:
        order=Orders.objects.get(order_id=order_id)
        order.delivery_status='Cancelled'
        order.save()
        messages.success(request,'Order Shipped successfully')
        return redirect(admin_orders)

@staff_login_required 
def user_details(request,order_id):
    details = Orders.objects.select_related('address').get(order_id=order_id)

    context={
        "details":details,
    }
    return render(request,'admin/user_details.html',context)

@staff_login_required 
def admin_return_products(request):
    products=ReturnProduct.objects.filter(status='Requested')
    context={
        "products":products,
    }
    return render(request,'admin/return_verification.html',context)

from user.models import wallet_history

@staff_login_required 
def approve_return(request,order_id):
    order=Orders.objects.get(order_id=order_id)
    user_profile=UserProfile.objects.get(user=order.user)
    return_status=ReturnProduct.objects.get(order=order)
    return_status.status='Approved'
    order.delivery_status='Returned'
    user_profile.wallet += order.total_price
    user_profile.save()
    return_status.save()
    order.save()

    wallet_history.objects.create(order_id=order.order_id,user=order.user,amount=order.total_price,reason='Return Product')
    
    if order.product.variant==True:
        variant_id=Product.objects.filter(variant_id=order.product.variant_id)
        for product in variant_id:
            product.stock += order.quantity*order.product.variant_quantity
            product.save()
    else:
        order.product.stock += order.quantity
        order.product.save()

    return redirect('admin_return_products')

@staff_login_required 
def Reject_return(request,order_id):
    order=Orders.objects.get(order_id=order_id)
    return_status=ReturnProduct.objects.get(order=order)
    return_status.status='Rejected'
    order.delivery_status='Rejected'
    return_status.save()
    order.save()
    return redirect('admin_return_products')


@staff_login_required 
def admin_reports(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    orders = Orders.objects.select_related('product').all()

    if start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])

    total_revenue = Orders.objects.filter(delivery_status='Delivered') \
                                   .aggregate(total=Sum('total_price'))['total'] or 0
    total_sales=orders.count()
    delivered=Orders.objects.filter(delivery_status='Delivered')
    total_delivered=delivered.count()
    context = {
        'total_orders': orders,
        'total_revenue': total_revenue,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales':total_sales,
        'total_delivered':total_delivered
    }
    return render(request, 'admin/admin_reports.html', context)


from django.utils import timezone
from datetime import timedelta


@staff_login_required 
def admin_reports_filter(request,status):
    # Set defaults
    total_orders = Orders.objects.none()
    total_revenue = 0
    total_sales = 0

    if status == "weekly":
        one_week_ago = timezone.now() - timedelta(days=7)
        total_orders = Orders.objects.filter(created_at__gte=one_week_ago)
        total_revenue = total_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_sales = total_orders.count()
    
    elif status == 'daily':
        one_day = timezone.now() -timedelta(days=1)
        total_orders = Orders.objects.filter(created_at__gte=one_day)
        total_revenue = total_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_sales = total_orders.count()
    
    elif status == 'monthly':
        one_month = timezone.now() - timedelta (days=30)
        total_orders = Orders.objects.filter(created_at__gte=one_month)
        total_revenue = total_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_sales = total_orders.count()
    
    elif status == 'yearly':
        one_year = timezone.now() - timedelta (days=365)
        total_orders = Orders.objects.filter(created_at__gte=one_year)
        total_revenue = total_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_sales = total_orders.count()

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_sales': total_sales,
    }
    return render(request, 'admin/admin_reports.html', context)

# sales report pdf download
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import datetime

def generate_pdf(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter only delivered orders
    orders = Orders.objects.select_related('product').filter(delivery_status='Delivered')

    # Validate and filter by date
    if start_date and end_date and start_date != "None" and end_date != "None":
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            orders = orders.filter(created_at__date__range=[start_date, end_date])
        except ValueError:
            pass

    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0

    template_path = 'admin/pdf_template.html'
    context = {
        'orders': orders,
        'total_revenue': total_revenue,
        'start_date': start_date,
        'end_date': end_date,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response



    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url="admin_login")
def log_out(request):
    logout(request)
    messages.success(request,'you have been log-out successfully.')
    return redirect('admin_login')


#admin operations..
from django.core.paginator import Paginator
from django.contrib.auth.models import User
@login_required(login_url="admin_login")
def admin_users(request):
    query = request.GET.get("search", "")  # Get search query

    if query:
        users = User.objects.filter(username__icontains=query)  # Search by username
    else:
        users = User.objects.all()

    # Pagination
    paginator = Paginator(users, 5) 
    page_number = request.GET.get("page")
    users_page = paginator.get_page(page_number)

    return render(request, "admin/admin_users.html", {"users": users_page, "query": query})


@login_required(login_url="admin_login")
def block_users(request,username):
    user=User.objects.get(username=username)
    user.is_active = not user.is_active  # Toggle block/unblock
    user.save()
    return redirect('admin_users')
    
@login_required(login_url="admin_login")
def interface(request):
    products=Product.objects.filter(offer_point=True)
    return render(request,'admin/user_interface.html',{"products":products})

@login_required(login_url="admin_login")
def add_offer(request):
    products=Product.objects.filter(offer_point=False)
    offer_products=Product.objects.filter(offer_point=True)
    context = {
        'products': products,
        'offer_products': offer_products,
    }
    return render(request,'admin/add_offer.html',context)

@login_required(login_url="admin_login")
def offer_products(request):
    if request.method == "POST":
        selected_product_ids = request.POST.getlist("products")  # Get selected products as a list
        selected_offer_products=request.POST.getlist('offer_products')

        offer_products=Product.objects.filter(id__in=selected_offer_products) 
        if offer_products.exists:
            for product in offer_products:
                Product.objects.filter(id=product.id).update(offer_point=False)
                messages.success(request,'product removed successfully')
                return redirect('interface')
        selected_products = Product.objects.filter(id__in=selected_product_ids)  # Fetch selected products
        if selected_products.exists():
            for product in selected_product_ids:
                Product.objects.filter(id=product).update(offer_point=True)
                messages.success(request,'product added successfully')
                return redirect('interface')
        
    return render(request,'admin/user_interface.html')

@staff_login_required 
def coupon(request):
    coupons=Coupons.objects.all()
    paginator = Paginator(coupons, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request,'admin/coupons.html',context)

@staff_login_required 
def add_coupon(request):
    if request.method=="POST":
        code=request.POST.get('coupon_code').capitalize()
        discount=request.POST.get("discount")
        min_order_price=request.POST.get("min_order_price")
        status=request.POST.get("status")

        try :
            Coupons.objects.get(coupon_no=code)
            messages.error(request,'coupon already exists')
            return redirect('coupon')
        except:
            pass

        create_coupon=Coupons.objects.get_or_create(coupon_no=code,discount_percentage=discount,min_order_price=min_order_price,status=status)
        messages.success(request,'added coupon successfully')
        return redirect('coupon')
    return render(request,'admin/add_coupon.html')

@staff_login_required 
def delete_coupon(request,coupon_id):
    coupon=Coupons.objects.get(id=coupon_id)
    coupon.delete()
    messages.success(request,'deleted coupon successfully')
    return redirect('coupon')


@staff_login_required 
def admin_view_orders(request):
    all_orders = Orders.objects.all().order_by('-created_at')
    
    return render(request,'admin/admin_view_orders.html',{"orders":all_orders})

@staff_login_required
def transaction_report(request):
    transaction_report=Orders.objects.all()
    total=Orders.objects.filter(delivery_status='Delivered') \
                    .aggregate(total=Sum('total_price'))['total'] or 0
    context={
        'transaction_report':transaction_report,
        'total':total
    }
    return render(request,'admin/transaction.html',context)

from decimal import Decimal
from products.models import Category_offers
@staff_login_required
def add_category_offer(request):
    if request.method == "POST":
        category_id = request.POST.get('category_id')
        offer_percentage_str = request.POST.get('offer_percentage')
        
        try:
            offer_percentage = Decimal(offer_percentage_str)
            category = categories.objects.get(id=category_id)

            # Avoid duplicate offer
            if Category_offers.objects.filter(category=category).exists():
                messages.warning(request, "Offer already exists for this category.")
                return redirect('add_category_offer')

            products = Product.objects.filter(category=category)

            backup_prices = {}
            for product in products:
                if product.offer_price is not None:
                    # Backup the original offer_price
                    backup_prices[str(product.id)] = str(product.offer_price)
                    
                    # Apply discount
                    discount = (product.offer_price * offer_percentage) / 100
                    new_price = product.offer_price - discount
                    
                    product.offer_price = new_price
                    product.save()

            # Save to Category_offers table
            Category_offers.objects.create(
                category=category,
                discount_percentage=offer_percentage,
                backup_prices=backup_prices
            )

            messages.success(request, f"{offer_percentage}% offer applied to '{category.name}' category.")
            return redirect('add_category_offer')

        except Exception as e:
            messages.error(request, "Failed to apply category offer.")

    # GET section
    category = categories.objects.all()
    active_offers = Category_offers.objects.select_related('category').all()
    context = {
        'category': category,
        'active_offers': active_offers
    }
    return render(request, 'admin/products/category_offer.html', context)
@staff_login_required
def delete_category_offer(request, offer_id):
    if request.method == "POST":
        offer = get_object_or_404(Category_offers, id=offer_id)
        category = offer.category

        backup_prices = offer.backup_prices
        products = Product.objects.filter(category=category)
        for product in products:
            if str(product.id) in backup_prices:
                product.offer_price = Decimal(str(backup_prices[str(product.id)]))
                product.save()

        offer.delete()
    return redirect('add_category_offer') 

@staff_login_required
def user_related_order_details(request,order_id):
    order = Orders.objects.get(order_id=order_id)
    return render(request, 'admin/order_detailed_details.html', {'order': order})


def most_selling_products(request):
   
    product_sales = Orders.objects.values('product__name') \
        .annotate(total_sold=Sum('quantity')) \
        .order_by('-total_sold')[:10] 

    labels = [item['product__name'] for item in product_sales]
    data = [item['total_sold'] for item in product_sales]

    context = {
        'labels': labels,
        'data': data,
    }
    return render(request, 'admin/most_selling.html', context)