from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.user_login,name='user_login'),
    path('user_home/',views.user_home,name='user_home'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('user_logout/',views.user_logout,name='user_logout'),
    path('referral_code/',views.referral_code,name='referral_code'),

    #forget password,otp
    path('forget_password/',views.forget_password,name='forget_password'),
    path('forget_otp/',views.forget_otp,name='forget_otp'),
    path('new_password/',views.new_password,name='new_password'),
    path('forget_resend_otp/',views.forget_resend_otp,name='forget_resend_otp'),

    #create account
    path('create_account/',views.create_account,name='create_account'),
    path('create_otp/',views.create_otp,name="create_otp"),
    path('create_user/',views.create_user,name="create_user"),
    path('resend_otp/',views.resend_otp,name="resend_otp"),


   path('list_products/<int:category>/',views.list_products,name='list_products'),
   path('list_products_on_search/<int:category>/<str:search_query>/',views.list_products,name='list_products_on_search'),
   path('sort/<str:sort>/',views.sort,name='sort'),
   path('sort/<str:sort>/<str:search_query>/',views.sort,name='sort_search'),
   path('clear_filter/',views.clear_filter,name='clear_filter'),
   path('clear_filter/<str:search_query>/',views.clear_filter,name='clear_filter_search'),
   path('user_product/<str:product>/',views.user_product,name='user_product'),
   path('product_variant/', views.product_variant, name='product_variant'),
   path('r_product/<int:product>/',views.r_product,name='r_product'),
   path('user_search_products/',views.user_search_products,name='user_search_products'),
   path('user_wallet/',views.user_wallet,name='user_wallet'),

    path('user_account/',views.user_account,name='user_account'),
    path('edit_account_otp/',views.edit_account_otp,name='edit_account_otp'),
    path('saved_address/',views.saved_address,name='saved_address'),
    path('add_address/',views.add_address,name='add_address'),
    path('address_addon/',views.address_addon,name='address_addon'),
    path('edit_address/<int:address_id>/',views.edit_address,name='edit_address'),
    path('delete_address/<int:address_id>/',views.delete_address,name='delete_address'),
]
