from django.urls import path
from . import admin_views

admin_urlpatterns = [
    # Dashboard
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Productos
    path('admin/products/', admin_views.admin_products_list, name='admin_products_list'),
    path('admin/products/create/', admin_views.admin_product_create, name='admin_product_create'),
    path('admin/products/<int:product_id>/edit/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/<int:product_id>/delete/', admin_views.admin_product_delete, name='admin_product_delete'),
    
    # Categorías
    path('admin/categories/', admin_views.admin_categories_list, name='admin_categories_list'),
    path('admin/categories/create/', admin_views.admin_category_create, name='admin_category_create'),
    path('admin/categories/<int:category_id>/edit/', admin_views.admin_category_edit, name='admin_category_edit'),
    path('admin/categories/<int:category_id>/delete/', admin_views.admin_category_delete, name='admin_category_delete'),
    
    # Imágenes de productos
    path('admin/products/<int:product_id>/images/', admin_views.admin_product_images, name='admin_product_images'),
    path('admin/images/<int:image_id>/delete/', admin_views.admin_image_delete, name='admin_image_delete'),
    path('admin/images/<int:image_id>/set-primary/', admin_views.admin_image_set_primary, name='admin_image_set_primary'),
]
