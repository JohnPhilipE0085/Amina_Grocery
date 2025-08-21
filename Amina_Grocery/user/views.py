from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.contrib.auth.models import User
from .models import OTPStorage
from django.core.mail import send_mail
from products.models import Product,categories
from user.models import UserProfile
from django.core.paginator import Paginator


# Create your views here.

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_login(request):
    if request.user.is_authenticated:
        return redirect('user_home')
    
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')

        user=authenticate(request,username=username,password=password,is_active=True)

        if user is not None:
            login(request,user)
            request.session['username']=user.username
            return redirect('user_home')
        else:
            messages.error(request,'invalid username or password')
            return redirect('user_login')

    return render(request,'user/user_login.html')

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def store_user_in_session(sender, request, user, **kwargs):
    request.session['username'] = user.username
    request.session['email'] = user.email

@login_required(login_url="user_login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_logout(request):
    logout(request)
    request.session.flush()
    messages.success(request,'You logged out successfully.')
    return redirect('user_login')


#forget password
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def forget_password(request):
    command = "forget password"
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)  
            
            if not user.has_usable_password(): 
                messages.error(request, 'User logged in using Google. Password reset is not possible.')
                return redirect('user_login')

            
            request.session['users_email'] = email 
            otp = OTPStorage.create_or_update_otp(email=email)

            subject = "Amina Grocery...Your OTP Code"
            
            message = f"Your OTP code for resetting password is {otp}. It will expire in 5 minutes."
            send_mail(subject, message, "johnphilipe085@gmail.com", [email])

            return redirect('forget_otp')

        except User.DoesNotExist:
            messages.error(request, 'User does not exist.')
            return redirect('forget_password')

    return render(request, 'user/email.html', {'command': command})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def forget_otp(request):
    command='forget password'
    users_email=request.session.get('users_email')

    if request.method == "POST":
        otp = request.POST.get("otp")

        try:
            otp_entry = OTPStorage.objects.get(email=users_email, otp=otp)
            if otp_entry.is_expired():
                messages.error(request,'otp has been expired check after 5 mins')
                return redirect('user_login')
            
            #if it is valid it redirect to create password
            return redirect('new_password')
        
        except OTPStorage.DoesNotExist:
            messages.error(request,'invalid otp')
            return redirect('forget_otp')

    return render(request,'user/otp.html',{"command":command})

def forget_resend_otp(request):
    command='forget password'
    email=request.session.get('users_email')
    otp = OTPStorage.create_or_update_otp(email=email)

    subject = "Amina Grocery...Your OTP Code "
    message = f"Your OTP code for resetting password is {otp}. It will expire in 5 minutes."
    send_mail(subject, message, "johnphilipe085@gmail.com", [email])
    messages.success(request,'otp resended')
    return redirect('forget_otp')
    

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def new_password(request):

    #fetch email id to delete the userdetails from the otp table
    email=request.session.get('users_email')
    delete_otp= OTPStorage.objects.get(email=email)

    if request.method=='POST':
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        if password!=confirm_password:
            messages.error(request,'passwords are not matching')
            return redirect('new_password')
        if len(password) < 8:
            messages.warning(request, "Password is too short (minimum 8 characters).")
            return redirect('new_password')
        elif not re.search(r"[A-Za-z]", password):
            messages.warning(request, "Password must contain at least one letter.")
            return redirect('new_password')
        elif not re.search(r"\d", password):
            messages.warning(request, "Password must contain at least one number.")
            return redirect('new_password')
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            messages.warning(request, "Password should contain at least one symbol.")
            return redirect('new_password')
        user=User.objects.get(email=email)
        user.set_password(confirm_password)
        user.save()
        delete_otp.delete()
        messages.success(request,'password changed successfully')
        return redirect('user_login')
        
    return render(request,'user/new_password.html')

#create account
import re
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_account(request):
    command='create account'
    if request.method=='POST':
        email=request.POST.get('email')
        
        user_exists=User.objects.filter(email=email).exists()

        if user_exists:
            messages.error(request,'you have already registered')
            return redirect('user_login')
        else:
            request.session['users_email'] = email #stores the email for the next step
            otp = OTPStorage.create_or_update_otp(email=email)

            subject = "Amina Grocery...Your OTP  Code "
            message = f"Your OTP code for creating new account is {otp}. It will expire in 5 minutes."
            cleaned_message=re.sub(r"\(Expires at .*?\)", "", message).strip()
            send_mail(subject, cleaned_message, "johnphilipe085@gmail.com", [email])

            return redirect('create_otp')

    return render(request,'user/email.html',{"command":command})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_otp(request):
    command='create account'
    users_email=request.session.get('users_email')

    if request.method == "POST":
        otp = request.POST.get("otp")

        try:
            otp_entry = OTPStorage.objects.get(email=users_email, otp=otp)
            if otp_entry.is_expired():
                messages.error(request,'otp has been expired check after 5 mins')
                return redirect('user_login')
            
            #if it is valid it redirect to create password
            return redirect('create_user')
        
        except OTPStorage.DoesNotExist:
            messages.error(request,'wrong credentails')
            return redirect('create_otp')

    return render(request,'user/otp.html',{"command":command})


def resend_otp(request):
    
    email=request.session.get('users_email')

    otp = OTPStorage.create_or_update_otp(email=email)

    subject = "Amina Grocery...Your OTP  Code "
    message = f"Your OTP code for creating new account is {otp}. It will expire in 5 minutes."
    send_mail(subject, message, "johnphilipe085@gmail.com", [email])
    messages.success(request,'otp resended successfully')
    return redirect('create_otp')

from django.views.decorators.cache import never_cache
@never_cache

def create_user(request):
    
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')

        #check wheather the password is write or wrong...
        if password != confirm_password:
            messages.error(request,'the password you entered is not matching...')
            return redirect('create_user')
        if len(password) < 8:
            messages.warning(request, "Password is too short (minimum 8 characters).")
            return redirect('create_user')
        elif not re.search(r"[A-Za-z]", password):
            messages.warning(request, "Password must contain at least one letter.")
            return redirect('create_user')
        elif not re.search(r"\d", password):
            messages.warning(request, "Password must contain at least one number.")
            return redirect('create_user')
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            messages.warning(request, "Password should contain at least one symbol.")
            return redirect('create_user')
        
        if User.objects.filter(username=username).exists():
            messages.error(request,'username already taken')
            return redirect(create_user)
        else:
            email=request.session.get('users_email')
            user=User.objects.create_user(username=username,email=email,password=password)
            user.save()

            messages.success(request,'created user successfully...')
            return redirect('user_login')
    
    return render(request,'user/create_account.html')


from django.db.models import Q
@login_required(login_url='user_login') 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_home(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if user_profile.first_time_login:
        return redirect('referral_code')


    offer_products=Product.objects.filter(offer_point=True,is_in_stock=True,variant_quantity=1)
    category=categories.objects.filter(is_active=True)
    suggested=Product.objects.filter(is_in_stock=True,variant_quantity=1)[:7]
    Fresh_products=Product.objects.filter(Q(category=17,is_in_stock=True,variant_quantity=1)|Q(is_in_stock=True,variant_quantity=1,category=16))
    context={
        "offer_products":offer_products,
        "category":category,
        "suggested":suggested,
        "fresh_products":Fresh_products
    }
    return render(request,'home/user_home.html',context)

@login_required(login_url="user_login")
def user_search_products(request):
        if request.method=="POST":
            search_query = request.POST.get('search_product')
        else: 
            search_query = request.GET.get('search_product' ,'')

        products=Product.objects.filter(name__icontains=search_query,variant_quantity=1)
        
        categorys=categories.objects.filter(is_active=True)
        
        paginator=Paginator(products,5)
        page_number=request.GET.get('page')
        page_obj=paginator.get_page(page_number)

        context={
                "products":page_obj,
                "page_obj": page_obj,
                "category":categorys,
                "search_query":search_query,
            }
    
        return render(request, 'home/list_products.html', context)


@login_required(login_url="user_login")
def list_products(request,category,search_query=None):
    request.session['category']=category

    categorys=categories.objects.filter(is_active=True)
    if search_query is not None:
        products=Product.objects.filter(category=category,variant_quantity=1,name__icontains=search_query)
        request.session['category']=category
    else:
        products=Product.objects.filter(category=category,variant_quantity=1)

    paginator=Paginator(products,5)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    
    context={
        'products': page_obj,
        'page_obj': page_obj,
        "category":categorys,
        "search_query":search_query
    }
    return render(request,'home/list_products.html',context)


def clear_filter(request,search_query=None):
    category=request.session.get('category')
    categorys=categories.objects.filter(is_active=True)
    
    if search_query is None:
        products = Product.objects.filter(category=category,variant_quantity=1)
    else:
        products=Product.objects.filter(name__icontains=search_query,variant_quantity=1)

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        "category": categorys,
        'search_query':search_query
    }
    return render(request, 'home/list_products.html', context)

@login_required(login_url="user_login")
def sort(request,sort,search_query=None):
    category=request.session.get('category')
    categorys=categories.objects.filter(is_active=True,id=category)
    
    if search_query is None:
        
        if sort == "lh":
            products = Product.objects.filter(category=category,variant_quantity=1).order_by('offer_price')
        elif sort == "hl":
            products = Product.objects.filter(category=category,variant_quantity=1).order_by("-offer_price")
        elif sort == "a-z":
            products = Product.objects.filter(category=category,variant_quantity=1).order_by("name")
        elif sort == "z-a":
            products = Product.objects.filter(category=category,variant_quantity=1).order_by("-name")
        else:
            products = Product.objects.all(variant_quantity=1)

        paginator = Paginator(products, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context={
            "products":page_obj,
            "category":categorys,
            'page_obj': page_obj,
            
        }
    else:
        categorys=categories.objects.filter(is_active=True)
        if sort == "lh":
            products = Product.objects.filter(name__icontains=search_query,variant_quantity=1).order_by('offer_price')
        elif sort == "hl":
            products = Product.objects.filter(name__icontains=search_query,variant_quantity=1).order_by("-offer_price")
        elif sort == "a-z":
            products = Product.objects.filter(name__icontains=search_query,variant_quantity=1).order_by("name")
        elif sort == "z-a":
            products = Product.objects.filter(name__icontains=search_query,variant_quantity=1).order_by("-name")
        else:
            products = Product.objects.all(variant_quantity=1)
        
        paginator = Paginator(products, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context={
            "products":page_obj,
            "category":categorys,
            'page_obj': page_obj,
            'search_query':search_query
        }
        
    
    return render(request,'home/list_products.html',context)

from django.db.models import Avg

from orders.models import WishList,Orders
@login_required(login_url="user_ login")
def user_product(request,product):
    product=Product.objects.get(name=product)
    rating=Orders.objects.filter(product=product).aggregate(Avg('rating')) 
    
    
    try:
        rating=int(rating['rating__avg'])
    except:
        rating=None

    reviews = Orders.objects.filter(product=product, reviewed=True)
    R_Products=Product.objects.filter(is_in_stock=True,variant_quantity=1)[:5]
    try:
        if_wishlist=WishList.objects.get(user=request.user,product=product)
    except:
        if_wishlist=None
    if product.variant==True:
        variants = Product.objects.filter(variant_id=product.variant_id).exclude(name=product.name)
    else:
        variants=None
    context={
        "product":product,
        "variants":variants,
        "R_Products":R_Products,
        'reviews':reviews,
        "wish_list":if_wishlist,
        "rating":rating
    }
    return render(request,'home/user_product.html',context)

@login_required(login_url='user_login')
def product_variant(request):
    if request.method=="POST": 
        variant_name=request.POST.get('variant_name')
        try:
            product=Product.objects.get(name=variant_name)
            return redirect('user_product',product=product.name)
        except:
            messages.error('variant not found')
            return redirect('home/user_home.html')

@login_required(login_url="user_login")
def r_product(request,product):
    product=Product.objects.get(id=product)
    R_Products= Product.objects.filter(variant_quantity=1)[:5]
    rating=Orders.objects.filter(product=product).aggregate(Avg('rating')) 
    try:
        rating=int(rating['rating__avg'])
    except:
        rating=0

    if product.variant==True:
        variants = Product.objects.filter(variant_id=product.variant_id).exclude(name=product.name)
    else:
        variants=None
    context={
        "product":product,
        "R_Products":R_Products,
        'variants':variants,
        "rating":rating
    }
    return render(request,"home/user_product.html",context)

@login_required(login_url="user_login")
def user_account(request):
    user=User.objects.get(username=request.user)
    if user.password[0]=="!":
        user_password='Google Logged-In'
    else:
        user_password=None

    # if there is any edit needed
    if request.method=="POST":
        username=request.POST.get('username')
        email=request.POST.get('email')
        old_password=request.POST.get('password')
        new_password=request.POST.get('new_password')
        
        # checks wheather the username is the same
        if username!=user.username:
            if User.objects.filter(username=username).exists():
                messages.error(request,'username is already taken try different username')
                return redirect('user_account')
            user.username=username
            user.save()
            messages.success(request,'Username Changed Successfully')
    
        #checks wheather the email is the same or not
        if email!=user.email:
            if User.objects.filter(email=email):
                messages.error(request,'This E-mail has been already registered')
                return redirect('user_account')
            otp = OTPStorage.create_or_update_otp(email=email)

            request.session['new_email']=email
            
            subject = "Amina Grocery...Your OTP Code "
            message = f"Your OTP code for resetting password is {otp}. It will expire in 5 minutes."
            send_mail(subject, message, "johnphilipe085@gmail.com", [email])

            return redirect('edit_account_otp')
        
        #checks wheather the password is same or not
        from django.contrib.auth.hashers import check_password

        if check_password(old_password, user.password):
            if len(new_password) < 8:
                messages.warning(request, "Password is too short (minimum 8 characters).")
                return redirect('user_account')
            elif not re.search(r"[A-Za-z]", new_password):
                messages.warning(request, "Password must contain at least one letter.")
                return redirect('user_account')
            elif not re.search(r"\d", new_password):
                messages.warning(request, "Password must contain at least one number.")
                return redirect('user_account')
            elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
                messages.warning(request, "Password should contain at least one symbol.")
                return redirect('user_account')
            else:
                user.set_password(new_password)  
                user.save()
                messages.success(request, 'Password changed successfully')
                return redirect('user_account')
        else:
            messages.error(request, 'Old password is incorrect')
            return redirect('user_account')
    context={
        "user":user,
        "user_password":user_password
        }
    return render(request,'user/user_page/user_details.html',context)

@login_required(login_url="user_login")
def edit_account_otp(request):
    command='edit_account_otp'
    if request.method == "POST":
        otp = request.POST.get("otp")

        try:
            email=request.session.get('new_email')
            otp_entry = OTPStorage.objects.get(email=email, otp=otp)
            if otp_entry.is_expired():
                messages.error(request,'otp has been expired check after 5 mins')
                return redirect('user_login')
            
            #if it is valid it redirect to create password
            user=User.objects.get(username=request.user)
            new_email=request.session.get('new_email')
            user.email=new_email
            user.save()
            return redirect('user_account')
        
        except OTPStorage.DoesNotExist:
            messages.error(request,'invalid otp')
            return redirect('edit_account_otp')

    return render(request,'user/otp.html',{"command":command})

# def search_product_filters(request):
    
from .models import address
@login_required(login_url="user_login")
def add_address(request):
    if request.method=="POST":
        full_name=request.POST.get('username').strip().capitalize()
        house_no=request.POST.get('house_no').strip().capitalize()
        phone_no=request.POST.get('phone_no')
        pincode=int(request.POST.get('pincode'))
        city=request.POST.get('city').strip().capitalize()
        place=request.POST.get('place').strip().capitalize()
        land_mark=request.POST.get('land_mark').strip().capitalize()

        available_pincode=[695001,682016,673020,676505,680613]
        if pincode not in available_pincode:
            messages.error(request,'There is no delivery to selected Pincode')
            return redirect('add_address')

        user_name=request.session.get('username')
        user=User.objects.get(username=user_name)
        add_address=address.objects.create(user=user,full_name=full_name,house_no=house_no,phone_no=phone_no,pincode=pincode,city=city,place=place,land_mark=land_mark)
        add_address.save()
        messages.success(request,'address added sucessfully')
        return redirect('saved_address')
        
    return render(request,'user/user_page/add_address.html')

@login_required(login_url="user_login")
def address_addon(request):
    if request.method=="POST":
        full_name=request.POST.get('username').strip().capitalize()
        house_no=request.POST.get('house_no').strip().capitalize()
        phone_no=request.POST.get('phone_no')
        pincode=int(request.POST.get('pincode'))
        city=request.POST.get('city').strip().capitalize()
        place=request.POST.get('place').strip().capitalize()
        land_mark=request.POST.get('land_mark').strip().capitalize()

        available_pincode=[695001,682016,673020,676505,680613]
        if pincode not in available_pincode:
            messages.error(request,'There is no delivery to the selected Pincode')
            return redirect('address_addon')
        
        user_name=request.session.get('username')
        user=User.objects.get(username=user_name)
        add_address=address.objects.create(user=user,full_name=full_name,house_no=house_no,phone_no=phone_no,pincode=pincode,city=city,place=place,land_mark=land_mark)
        add_address.save()
        messages.success(request,'address added sucessfully')
        return redirect('place_order')
        
    return render(request,'user/user_page/address_addon.html')


@login_required(login_url="user_login")
def saved_address(request):
    username=request.session.get('username')
    user=User.objects.get(username=username)
    user_address=address.objects.filter(user=user)
    return render(request,'user/user_page/saved_address.html',{"user_address":user_address})
@login_required(login_url="user_login")
def edit_address(request,address_id):
    current_address=address.objects.get(id=address_id)
    if request.method=="POST":
        full_name=request.POST.get('username').strip().capitalize()
        house_no=request.POST.get('house_no').strip().capitalize()
        phone_no=request.POST.get('phone_no')
        pincode=request.POST.get('pincode')
        city=request.POST.get('city').strip().capitalize()
        place=request.POST.get('place').strip().capitalize()
        land_mark=request.POST.get('land_mark').strip().capitalize()

        address.objects.filter(id=address_id).update(full_name=full_name,house_no=house_no,phone_no=phone_no,pincode=pincode,city=city,place=place,land_mark=land_mark)

        return redirect('saved_address')
    return render(request,'user/user_page/edit_address.html',{"current_address":current_address})
@login_required(login_url="user_login")
def delete_address(request,address_id):
    del_address=address.objects.get(id=address_id)
    del_address.delete()
    messages.success(request,'address deleted successfully')
    return redirect('saved_address')

from .models import wallet_history
@login_required(login_url="user_login")
def user_wallet(request):
    user=request.user
    user_profile=UserProfile.objects.get(user=user)
    wallet_amount=user_profile.wallet
    referral_code=user_profile.referral_code
    wallet_histories = wallet_history.objects.filter(user=request.user)

    context={
        'wallet_amount': wallet_amount,
        'referral_code':referral_code,
        'wallet_history':wallet_histories
    }
    return render(request,'user/user_page/user_wallet.html',context)

from .models import UserProfile
@login_required(login_url="user_login")
def referral_code(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user_profile.first_time_login = False
    user_profile.save()

    if request.method == 'POST':
        code = request.POST.get('referral_code')

        # Prevent self-referral
        if code == user_profile.referral_code:
            messages.error(request, "You cannot use your own referral code.")
            return render(request, 'user/referral_code.html')

        try:
            referral_check = UserProfile.objects.get(referral_code=code)
            referral_check.wallet += 250
            referral_check.save()
            messages.success(request, "Referral applied! ₹250 added to the referrer’s wallet.")
            return redirect('user_home')
        except UserProfile.DoesNotExist:
            messages.error(request, "Invalid referral code. Please try again.")
            return render(request, 'user/referral_code.html')

    return render(request, 'user/referral_code.html')

