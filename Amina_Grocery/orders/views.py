from http import client
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from .models import Cart,WishList,Orders,ReturnProduct
from products.models import Product
from django.contrib import messages
from django.urls import reverse
from admins.models import Coupons
from django.db.models import F, Sum
from user.models import address
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
import random
from user.models import UserProfile
# razorpay
from django.conf import settings
import razorpay



# Create your views here.
@login_required(login_url="user_login")
def add_to_wishlist(request,product_id):
    products=Product.objects.get(id=product_id)
    cart_item=Cart.objects.filter(user=request.user,product=products)
    if cart_item.exists():
        messages.error(request,'already added to Cart')
        product=products.name
        return redirect(reverse('user_product',args=[product]))


    add_to_wishlist=WishList.objects.get_or_create(user=request.user,product=products)
    messages.success(request,'Product Added to wishlist Successfully..')
    product=products.name
    return redirect(reverse('user_product',args=[product]))

@login_required(login_url="user_login")
def wish_list(request):
    wish_list = WishList.objects.select_related('product').filter(user=request.user)
    return render(request,'user/user_page/user_wishlist.html',{'wish_list':wish_list})

@login_required(login_url="user_login")
def remove_wishlist(request,product_id):
    wish_list=WishList.objects.get(user=request.user,product=product_id)
    wish_list.delete()
    messages.success(request,'removed product successfully')
    return redirect('wish_list')

@login_required(login_url="user_login")
def add_to_cart(request, product_id):
    user = User.objects.get(username=request.user)
    product = Product.objects.get(id=product_id)

    cart_item,created=Cart.objects.get_or_create(user=user,product=product)

    if not created:
        if product.stock>cart_item.quantity:
            if cart_item.quantity<5:
                cart_item.quantity += 1
                cart_item.save()
                
            else:
                messages.error(request,'product has reached its maximum limit')
                return redirect('user_product',product=product.name)
        else:
            messages.error(request,'Product reached its maximum stock quantity')
            return redirect(reverse('user_product', args=[product.name]))

    wishlist_item = WishList.objects.filter(user=request.user, product=product)
    if wishlist_item.exists():
        wishlist_item.delete()

    messages.success(request,'Product added to cart successfully')
    return redirect(reverse('user_product', args=[product.name]))

def add_to_cart_wishlist(request,product_id):
    user=User.objects.get(username=request.user)
    product = Product.objects.get(id=product_id)

    cart_item,created=Cart.objects.get_or_create(user=user,product=product)

    if not created:
        if product.stock>cart_item.quantity:
            if cart_item.quantity<5:
                cart_item.quantity += 1
                cart_item.save()
                
            else:
                messages.error(request,'product has reached its maximum limit')
                return redirect('user_product',product=product.name)
        else:
            messages.error(request,'Product reached its maximum stock quantity')
            return redirect(reverse('user_product', args=[product.name]))
        
    wishlist_item = WishList.objects.filter(user=request.user, product=product)
    if wishlist_item.exists():
        wishlist_item.delete()

    messages.success(request,'Product added to cart successfully')
    return redirect('wish_list')
    

@login_required(login_url="user_login")
def user_cart(request):
    try:
        selected_coupon=request.session.get('coupon')
        find_coupon=Coupons.objects.get(coupon_no=selected_coupon)
        coupon_discount=find_coupon.discount_percentage
    except:
        coupon_discount=0

    try:
        products=Cart.objects.filter(user=request.user,product__is_in_stock=True)
        mrp_price=Cart.objects.filter(user=request.user,product__is_in_stock=True).aggregate(
            total_cart_price=Sum(F('quantity')*F('product__price'))
        )['total_cart_price']

        grand_total = Cart.objects.filter(user=request.user,product__is_in_stock=True).aggregate(
        total_cart_price=Sum(F('quantity') * F('product__offer_price'))
        )['total_cart_price'] 

        discount=mrp_price-grand_total
        before_coupon_price=grand_total
        grand_total= grand_total-(grand_total*coupon_discount/100)
        after_coupon_price=before_coupon_price-grand_total
        coupons=Coupons.objects.all()
        

        context={
            'cart_items':products,
            'grand_total':grand_total,
            'mrp_price':mrp_price,
            'discount':discount,
            'coupons':coupons,
            'coupon_discount':after_coupon_price,
            'applied_coupon':selected_coupon
        }
    except:
        context={
            
        }
    
    return render(request,'user/user_page/user_cart.html',context)

@login_required(login_url="user_login")
def coupon_add(request):
    mrp_price=Cart.objects.filter(user=request.user,product__is_in_stock=True).aggregate(
        total_cart_price=Sum(F('quantity')*F('product__price'))
        )['total_cart_price']
    if request.method == "POST":
        coupon=request.POST.get('coupon')
        try:
            coupon_condition=Coupons.objects.get(coupon_no=coupon)
            if coupon_condition.min_order_price>mrp_price:
                messages.success(request,f"Coupon is Applicable on orders above ₹{coupon_condition.min_order_price}")
                request.session['coupon']=0
                return redirect('user_cart')
        except:
            pass
        request.session['coupon']=coupon
        messages.success(request,'Coupon applied successfully')
    return redirect('user_cart')

@login_required(login_url="user_login")
def remove_cart_item(request):
    if request.method=="POST":
        product_id=request.POST.get('product_id')
        product=Product.objects.get(id=product_id)
        remove_product=Cart.objects.get(user=request.user,product=product)
        remove_product.delete()
        messages.success(request,'removed product successfully')
    return redirect("user_cart")

@login_required(login_url="user_login")
def place_order(request):
    try:
        selected_coupon=request.session.get('coupon')
        find_coupon=Coupons.objects.get(coupon_no=selected_coupon)
        coupon_discount=find_coupon.discount_percentage
    except:
        coupon_discount=0


    products=Cart.objects.filter(user=request.user,product__is_in_stock=True)

    mrp_price=Cart.objects.filter(user=request.user,product__is_in_stock=True).aggregate(
        total_cart_price=Sum(F('quantity')*F('product__price'))
    )['total_cart_price']

    grand_total = Cart.objects.filter(user=request.user,product__is_in_stock=True).aggregate(total_cart_price=Sum(F('quantity') * F('product__offer_price')))['total_cart_price']

    discount=mrp_price-grand_total
    coupon_before_price=grand_total
    grand_total=grand_total-(grand_total*coupon_discount/100)
    coupon_after_price=coupon_before_price-grand_total
    addres=address.objects.filter(user=request.user)

    context={
        'products':products,
        'grand_total':grand_total,
        'mrp_price':mrp_price,
        'discount':discount,
        'address':addres,
        'coupon_offer':coupon_after_price,
    }

    return render(request,'user/user_page/place_order.html',context)

client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


@login_required(login_url="user_login")
def confirm_order(request):
    if request.method == "POST":
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        selected_address_id = request.POST.get('selected_address')
        payment_method = request.POST.get("payment_method")

        if not selected_address_id:
            messages.error(request, 'You cannot move forward without adding address')
            return redirect('place_order')

        try:
            coupon = request.session.get('coupon')
            coupon_no = Coupons.objects.get(coupon_no=coupon)
            coupon_discount = coupon_no.discount_percentage
        except:
            coupon_discount = 0
        request.session['coupon_discount'] = coupon_discount

        # Grand total
        grand_total = Cart.objects.filter(user=user, product__is_in_stock=True).aggregate(
            total_cart_price=Sum(F('quantity') * F('product__offer_price'))
        )['total_cart_price'] 
        
        grand_total -= (grand_total * coupon_discount / 100)
        
        # Save details for later (razorpay, etc.)
        request.session['grand_total'] = float(grand_total)
        request.session['address_id'] = selected_address_id

        # Payment method handling
        if payment_method == "cod":
            if grand_total < 1000:
                messages.error(request, 'Cash on Delivery is available for orders above ₹1000.')
                return redirect('place_order')
            p_method = 'cod'

        elif payment_method == 'wallet_pay':
            if user_profile.wallet < grand_total:
                messages.error(request, 'Insufficient balance on wallet')
                return redirect('place_order')
            user_profile.wallet -= grand_total
            user_profile.save()
            p_method = 'wallet_pay'

        elif payment_method == 'razorpay':
            amount = int(grand_total * 100)
            # Create a Razorpay Order
            razorpay_order = client.order.create(dict(amount=amount,
                                                       currency="INR",
                                                       payment_capture='1'))

            # order id of newly created order.
            razorpay_order_id = razorpay_order['id']
            callback_url = '/paymenthandler/'

            context = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_merchant_key':settings.RAZOR_KEY_ID,
                'razorpay_amount': amount,
                'currency':"INR",
                'callback_url':callback_url
            }
            return render(request,'user/user_page/payment_sample.html',context)
        
        try:
            user_address = address.objects.get(id=selected_address_id)
        except address.DoesNotExist:
            messages.error(request, "Invalid address selection.")
            return redirect('some_error_page')

        create_order(user, user_address, coupon_discount, p_method)

        messages.success(request, 'Order Placed Successfully...')
        return render(request, 'user/user_page/thank_you.html')


def create_order(user, selected_address, coupon_discount, payment_method):
    cart_id = random.randint(1000, 10000) * random.randint(1, 10000)
    cart_items = Cart.objects.filter(user=user)

    for item in cart_items:
        product = item.product
        quantity = item.quantity
        stock_quantity = product.variant_quantity * quantity
        price = product.offer_price * quantity
        if coupon_discount != 0:
            discounted_price = price - ((price * coupon_discount) / 100)
        else:
            discounted_price=0
        if product.variant:
            variant_products = Product.objects.filter(variant_id=product.variant_id)
            for prod in variant_products:
                prod.stock -= stock_quantity
                prod.save()
        else:
            product.stock -= quantity
            product.save()

        Orders.objects.create(
            user=user,
            product=product,
            quantity=quantity,
            cart_id=cart_id,
            price=price,
            discount_price=discounted_price,
            address=selected_address,
            payment_option=payment_method,
        )
    
    cart_items.delete()



from collections import defaultdict
@login_required(login_url="user_login")
def user_orders(request):
    orders = Orders.objects.filter(user=request.user)

    grouped_orders = defaultdict(list)

    for order in orders:
        grouped_orders[order.cart_id].append(order)

    # Convert to regular dict before sending to template
    grouped_orders = dict(grouped_orders)

    context={'grouped_orders':grouped_orders}

    return render(request,'user/user_page/order_grouped_items.html',context)

@login_required(login_url='user_login')
def order_details(request,cart_id):
    product=Orders.objects.filter(user=request.user,cart_id=cart_id)
    context={'purchased_products':product,'cart_id':cart_id}
    return render(request,'user/user_page/user_orders.html',context)

@login_required(login_url="user_login")
def return_product(request,order_id):
    command='return_product'

    context={
        'command':command,
        'order_id':order_id,
    }

    if request.method=="POST":
        reason = request.POST.get("reason")
        image = request.FILES.get('image')
        order=Orders.objects.get(order_id=order_id)
        
        ReturnProduct.objects.create(order=order, reason=reason, images=image)
        order.delivery_status = "Requested"
        order.save()
        return redirect('user_orders')

    return render(request,'user/user_page/return_reason.html',context)

from user.models import wallet_history

@login_required(login_url="user_login")
def cancel_product(request,order_id):
    user_profile=UserProfile.objects.get(user=request.user)
    order=Orders.objects.get(order_id=order_id)
    order.delivery_status='Cancelled'
    order.save()

    wallet_history.objects.create(order_id=order.order_id,user=request.user,amount=order.total_price,reason='Cancelled Product')
    
    if order.payment_option=='razorpay' or order.payment_option=='wallet_pay':
        user_profile.wallet += order.total_price
        user_profile.save()
    
    product_quantity=order.product.variant_quantity*order.quantity
    if order.product.variant==True:
        variant_id=Product.objects.filter(variant_id=order.product.variant_id)
        for product in variant_id:
            product.stock += product_quantity
            product.save()
    else:
        order.product.stock += product_quantity
        order.product.save()
    messages.success(request,'the selected order is successfully cancelled')
    return redirect('user_orders')



from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
@login_required(login_url="user_login")
def generate_invoice(request, cart_id):
    orders = Orders.objects.filter(cart_id=cart_id).exclude(delivery_status__in=["Cancelled", "Returned"])
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{cart_id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    pdf.setFont("DejaVuSans", 20)
    pdf.drawString(40, height - 50, "Amina Grocery Store")
    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(40, height - 70, "Invoice")
    pdf.line(40, height - 75, width - 40, height - 75)

    y_cursor = height - 100
    pdf.setFont("DejaVuSans", 11)
    pdf.drawString(40, y_cursor, f"Order ID: {cart_id}")

    if orders.exists():
        first_order = orders.first()
        addr = first_order.address

        y_cursor -= 15
        pdf.drawString(40, y_cursor, f"Customer: {addr.full_name}")

        y_cursor -= 15
        address_line = f"{addr.house_no}, {addr.place}, {addr.city}"
        pdf.drawString(40, y_cursor, f"Address: {address_line}")

        y_cursor -= 15
        pdf.drawString(40, y_cursor, f"Phone: {addr.phone_no}")

        y_cursor -= 15
        pdf.drawString(40, y_cursor, f"Pincode: {addr.pincode}")

        y_cursor -= 15
        pdf.drawString(40, y_cursor, f"Landmark: {addr.land_mark}")

        y_cursor -= 15
        pdf.drawString(40, y_cursor, f"Date: {first_order.created_at.strftime('%Y-%m-%d')}")
    else:
        y_cursor -= 15
        pdf.drawString(40, y_cursor, "No orders found.")

    y_cursor -= 30
    data = [['Product', 'Qty', 'MRP', 'Offer', 'Saved', 'Discounted Price', 'Total']]

    actual_amount = 0
    total_saved = 0
    total_offer_price = 0

    for order in orders:
        product = order.product
        qty = order.quantity
        mrp = product.price
        offer = product.offer_price
        
        # Savings from offer
        saved_offer = (mrp - offer) * qty
        discounted_price = order.discount_price  # This is the discount applied on total price (coupon or extra)
        total = order.total_price

        # total_saved = offer saving + discounted_price (discount_price is already the total discount on this product)
        saved = saved_offer + discounted_price

        actual_amount += mrp * qty
        total_saved += saved
        total_offer_price += total

        data.append([
            str(product),
            str(qty),
            f"₹{mrp:.2f}",
            f"₹{offer:.2f}",
            f"₹{saved:.2f}",
            f"₹{discounted_price:.2f}",
            f"₹{total:.2f}"
        ])

    table = Table(data, colWidths=[130, 40, 60, 60, 60, 90, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    table_width, table_height = table.wrap(0, 0)
    table.drawOn(pdf, 40, y_cursor - table_height)
    summary_y = y_cursor - table_height - 30

    payment_option = first_order.payment_option if orders.exists() else 'N/A'

    if summary_y < 100:
        pdf.showPage()
        summary_y = height - 100

    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(40, summary_y, f"Actual Amount: ₹{actual_amount:.2f}")
    pdf.drawString(40, summary_y - 15, f"Total Saved: ₹{total_saved:.2f}")
    pdf.drawString(40, summary_y - 30, f"Total Amount to Pay: ₹{total_offer_price:.2f}")
    pdf.drawString(40, summary_y - 45, f"Payment Method: {payment_option}")

    pdf.setFont("DejaVuSans", 10)
    pdf.drawString(40, 50, "Thank you for shopping with us!")
    pdf.drawString(40, 35, "For support, contact support@mygroceryshop.com")

    pdf.showPage()
    pdf.save()
    return response



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url="user_login")
def payment_failed(request):
    return render(request, 'user/user_page/razorpay_failed.html')




#to increase and decrease the quantitiy in Cart
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@require_POST
@csrf_exempt  
def update_cart(request):
    product_id = request.POST.get('product_id')
    action = request.POST.get('action')

    product = Product.objects.get(id=product_id)
    cart_qs = Cart.objects.filter(user=request.user, product=product)

    if not cart_qs.exists():
        return JsonResponse({'error': 'Cart item not found'}, status=404)

    cart_item = cart_qs.first()

    if action == 'increment': 
        if cart_item.quantity < 5 and product.stock>cart_item.quantity:
            cart_qs.update(quantity=F('quantity') + 1)
        else:
            return JsonResponse({'error':'maximum quantity reached get lost'},status=400)
    elif action == 'decrement' and cart_item.quantity > 1:
        cart_qs.update(quantity=F('quantity') - 1)

    cart_item.refresh_from_db()

    # Recalculate all prices for current user's cart
    cart_items = Cart.objects.filter(user=request.user)
    
    mrp_price = sum(item.product.price * item.quantity for item in cart_items)
    discount = sum((item.product.price - item.product.offer_price) * item.quantity for item in cart_items)
    coupon_discount = 0  # Replace with your actual coupon logic if needed
    grand_total = mrp_price - discount - coupon_discount

    return JsonResponse({
        'new_quantity': cart_item.quantity,
        'mrp_price': f'{mrp_price:.2f}',
        'discount': f'{discount:.2f}',
        'coupon_discount': f'{coupon_discount:.2f}',
        'grand_total': f'{grand_total:.2f}'
    })



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url="user_login")
def user_review(request, order_id):
    order_details = get_object_or_404(Orders, order_id=order_id)

    if request.method == "POST":
        review = request.POST.get('review')
        rating = request.POST.get('rating')
        order_details.rating=rating
        order_details.review = review
        order_details.reviewed = True  
        order_details.save()
        messages.success(request, 'Review Successfully Updated')
        return redirect('user_orders')  
    context = {
        'order_id': order_id,  
        'order': order_details  
    }
    return render(request, 'user/user_page/user_review.html', context)
   


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url="user_login")
def edit_review(request, order_id):
    # Fetch the order object, make sure it exists
    order_details = get_object_or_404(Orders, order_id=order_id)

    # Check if the order has already been reviewed
    if not order_details.reviewed:
        messages.warning(request, "You haven't written a review for this order yet.")
        return redirect('user_orders')

    if request.method == "POST":
        # Get the updated review from the form
        updated_review = request.POST.get('review')
        edited_rating = request.POST.get('rating')
        order_details.rating = edited_rating
        order_details.review = updated_review
        order_details.save()
        messages.success(request, 'Review Successfully Updated')
        return redirect('user_orders')

    # Pre-fill the form with the existing review
    context = {
        'order_id': order_id,
        'order': order_details,  # This contains the existing review
    }
    return render(request, 'user/user_page/edit_review.html', context)


def delete_review(request,order_id):
    order_details=Orders.objects.get(order_id=order_id)
    order_details.reviewed=False
    order_details.review= None
    order_details.rating= None
    order_details.save()
    messages.success(request,'Deleted Review Successfully')
    return redirect('user_orders')

# payment/views.py

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from razorpay.errors import SignatureVerificationError

@csrf_exempt
def paymenthandler(request):
    user = request.user
    user_address_id = request.session.get('address_id')
    coupon_discount = request.session.get('coupon_discount', 0)

    # Ensure address exists
    try:
        user_address = address.objects.get(id=user_address_id)
    except address.DoesNotExist:
        return HttpResponseBadRequest("Invalid address")

    if request.method == "POST":
        try:
            # Collect payment parameters
            payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            if not all([payment_id, razorpay_order_id, signature]):
                return HttpResponseBadRequest("Missing payment details")

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # Verify signature (raises error if invalid)
            client.utility.verify_payment_signature(params_dict)

            # If valid, create order
            create_order(user, user_address, coupon_discount, 'razorpay')
            return render(request, 'user/user_page/razorpay_success.html')

        except SignatureVerificationError:
            # Signature failed (tampered or invalid payment)
            return render(request, 'user/user_page/razorpay_failed.html')

        except Exception as e:
            # Log unexpected errors
            return HttpResponseBadRequest("Something went wrong")
    else:
        return HttpResponseBadRequest("Only POST request is allowed")