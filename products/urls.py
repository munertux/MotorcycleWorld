from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product URLs
    path('featured/', views.featured_products, name='featured_products'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('bulk-update/', views.bulk_update_products, name='bulk_update_products'),
    path('', views.ProductListView.as_view(), name='product_list'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/tree/', views.CategoryTreeView.as_view(), name='category_tree'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Product Image URLs
    path('images/', views.ProductImageListView.as_view(), name='product_image_list'),
    path('images/<int:pk>/', views.ProductImageDetailView.as_view(), name='product_image_detail'),
    
    # Product Variant URLs
    path('variants/', views.ProductVariantListView.as_view(), name='product_variant_list'),
    path('variants/<int:pk>/', views.ProductVariantDetailView.as_view(), name='product_variant_detail'),
]
