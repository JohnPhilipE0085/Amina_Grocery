from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('add-product/',views.add_product, name='add_product'),
    path('add-variants/',views.add_variants,name='add_variants'),
    # path('products/', product_list, name='product_list'),
    path('admin_products/',views.admin_products,name='admin_products'),
    path('product/<int:product_id>/',views.product,name='product'),
    path('edit_product_option/<int:product_id>/',views.edit_product_option,name='edit_product_option'),
    path('edit_product/',views.edit_product,name='edit_product'),
    path('delete_product/',views.delete_product,name='delete_product'),
    path('activate_product/',views.activate_product,name='activate_product'),
    path('search_product/',views.search_product,name='search_product'),
    path('product_category/',views.product_category,name='product_category'),
    path('delete_category/<str:category>/',views.delete_category,name='delete_category'),
    path('active_category/<str:category>/',views.activate_category,name='activate_category'),
    path('edit_category/',views.edit_category,name='edit_category'),
]

# Append media URL configuration correctly
if settings.DEBUG:  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

