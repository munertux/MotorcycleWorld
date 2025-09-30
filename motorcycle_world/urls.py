"""
URL configuration for motorcycle_world project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from users.admin_auth import admin_login_view
from products.product_views import product_detail_view, add_review, get_product_reviews
from products.home_views import HomeView, category_products_view

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API routes  
    path('api/auth/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/reviews/', include('reviews.urls')),
    
    # Panel de administración personalizado (namespace único para evitar conflicto con django.contrib.admin)
    path('panel-admin/', include('products.admin_panel_urls', namespace='panel_admin')),
    
    # Authentication routes
    path('accounts/login/', admin_login_view, name='admin_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Frontend routes (Django templates)
    path('', HomeView.as_view(), name='home'),
    path('categoria/<slug:category_slug>/', category_products_view, name='category_products'),
    path('shop/', TemplateView.as_view(template_name='products.html'), name='products'),
    path('producto/<int:product_id>/', product_detail_view, name='product_detail'),
    path('cart/', TemplateView.as_view(template_name='cart.html'), name='cart'),
    path('checkout/', TemplateView.as_view(template_name='checkout.html'), name='checkout'),
    path('orders/', TemplateView.as_view(template_name='orders.html'), name='orders'),
    path('orders/<uuid:order_id>/', TemplateView.as_view(template_name='order_detail.html'), name='order_detail'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    
    # AJAX endpoints para reseñas
    path('ajax/product/<int:product_id>/review/', add_review, name='add_review'),
    path('ajax/product/<int:product_id>/reviews/', get_product_reviews, name='get_reviews'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
