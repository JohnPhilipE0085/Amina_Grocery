from django.urls import path
from .import views

urlpatterns = [
    path('wish_list/',views.wish_list,name='wish_list'),
    path('add_to_wishlist/<int:product_id>',views.add_to_wishlist,name='add_to_wishlist'),
    path('remove_wishlist/<int:product_id>',views.remove_wishlist,name='remove_wishlist'),
    path('add_to_cart/<int:product_id>/',views.add_to_cart,name='add_to_cart'),
    path('add_to_cart_wishlist/<int:product_id>/',views.add_to_cart_wishlist,name='add_to_cart_wishlist'),
    path('user_cart/',views.user_cart,name='user_cart'),
    path('remove_cart_item/',views.remove_cart_item,name='remove_cart_item'),
    path('coupon_add/',views.coupon_add,name='coupon_add'),
    path('place_order/',views.place_order,name='place_order'),
    path('confirm_order/',views.confirm_order,name='confirm_order'),
    path('invoice/<int:cart_id>/',views.generate_invoice, name='generate_invoice'),

    path('user_orders/',views.user_orders,name='user_orders'),
    path('order_details/<int:cart_id>',views.order_details,name='order_details'),
    path('return_product/<uuid:order_id>/',views.return_product,name='return_product'),
    path('cancel_product/<uuid:order_id>/',views.cancel_product,name='cancel_product'),
    
    #razorpay urls
    # path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('update-cart/', views.update_cart, name='update_cart'),
    

    path('user_review/<uuid:order_id>/',views.user_review,name='user_review'),
    path('edit_review/<uuid:order_id>/',views.edit_review,name='edit_review'),
    path('delete_review/<uuid:order_id>/',views.delete_review,name='delete_review'),

    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),
    ]
