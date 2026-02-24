from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admins/',views.admin_login,name='admin_login'),
    path('admin_home/',views.admin_home,name='admin_home'),
    path('admin_users/',views.admin_users,name='admin_users'),
    path('admin_orders/',views.admin_orders,name='admin_orders'),
    path('interface/',views.interface,name='interface'),
    path('add_offer/',views.add_offer,name='add_offer'),
    path('coupon/',views.coupon,name='coupon'),
    path('add_coupon/',views.add_coupon,name='add_coupon'),
    path('delete_coupon/<int:coupon_id>/',views.delete_coupon,name='delete_coupon'),
    path('offer_products/',views.offer_products,name='offer_products'),
    
    path('admin_reports/',views.admin_reports,name='admin_reports'),
    path('admin_reports_filter/<str:status>/',views.admin_reports_filter,name='admin_reports_filter'),
    path('log_out/',views.log_out,name='log_out'),
    path('best_selling/<str:product>/',views.best_selling,name='best_selling'),
    path('transaction_report/',views.transaction_report,name='transaction_report'),


    # user_operations
    path("block_users/<str:username>/",views.block_users, name="block_users"), 

    path('order_status_update/<uuid:order_id>/<str:status>/',views.order_status_update,name='order_status_update'),
    path('user_details/<uuid:order_id>/',views.user_details,name='user_details'),
    path('admin_return_products/',views.admin_return_products,name='admin_return_products'),
    path('approve_return/<uuid:order_id>/',views.approve_return,name='approve_return'),
    path('Reject_return/<uuid:order_id>/',views.Reject_return,name='Reject_return'),

    path('admin_view_orders/',views.admin_view_orders,name='admin_view_orders'),

    path('admin_reports/pdf/', views.generate_pdf, name='generate_pdf'),
    path('add_category_offer/',views.add_category_offer,name='add_category_offer'),
    path('delete_category_offer/<int:offer_id>/', views.delete_category_offer, name='delete_category_offer'),
    path('user_related_order_details/<uuid:order_id>/',views.user_related_order_details,name='user_related_order_details'),

    path('most_selling/', views.most_selling_products, name='most_selling_products'),

]
