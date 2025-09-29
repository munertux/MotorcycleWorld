from django.urls import path
from . import admin_views

app_name = 'panel_admin'

urlpatterns = [
    # Dashboard
    path('dashboard/', admin_views.admin_dashboard, name='dashboard'),
    
    # Productos
    path('products/', admin_views.admin_products_list, name='products_list'),
    path('products/create/', admin_views.admin_product_create, name='product_create'),
    path('products/<int:product_id>/edit/', admin_views.admin_product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', admin_views.admin_product_delete, name='product_delete'),
    
    # Categorías
    path('categories/', admin_views.admin_categories_list, name='categories_list'),
    path('categories/create/', admin_views.admin_category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', admin_views.admin_category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', admin_views.admin_category_delete, name='category_delete'),
    
    # Imágenes de productos
    path('products/<int:product_id>/images/', admin_views.admin_product_images, name='product_images'),
    path('images/<int:image_id>/delete/', admin_views.admin_image_delete, name='image_delete'),
    path('images/<int:image_id>/set-primary/', admin_views.admin_image_set_primary, name='image_set_primary'),
]
