from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db import models
from django.forms import TextInput, Textarea
from .models import Category, Product, ProductImage, ProductVariant


class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category management with hierarchical display.
    """
    list_display = ['name', 'parent', 'level_indicator', 'is_active', 'product_count', 'sort_order', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'sort_order']
    ordering = ['parent__name', 'sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Display', {
            'fields': ('image', 'is_active', 'sort_order')
        }),
    )
    
    def level_indicator(self, obj):
        """Visual indicator of category level"""
        level = obj.level
        indicator = "—" * level + " " if level > 0 else ""
        return format_html(f'<span style="color: #666;">{indicator}</span>{obj.name}')
    level_indicator.short_description = 'Hierarchy'
    
    def product_count(self, obj):
        """Show number of products in this category"""
        count = obj.products.count()
        if count > 0:
            return format_html(
                '<a href="/admin/products/product/?category__id__exact={}" style="color: #0066cc;">{} products</a>',
                obj.id, count
            )
        return "0 products"
    product_count.short_description = 'Products'
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('parent').prefetch_related('products')


class ProductImageInline(admin.TabularInline):
    """
    Inline interface for managing product images.
    """
    model = ProductImage
    extra = 1
    max_num = 10
    fields = ['image', 'alt_text', 'is_primary']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Show thumbnail preview of images"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    """
    Inline interface for managing product variants.
    """
    model = ProductVariant
    extra = 0
    fields = ['name', 'sku', 'price_adjustment', 'stock', 'attributes', 'is_active']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
    }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Comprehensive admin interface for Product management.
    """
    list_display = [
        'name', 'sku', 'category', 'price_display', 'stock_info', 
        'status', 'is_featured', 'rating_display', 'created_at'
    ]
    list_filter = [
        'status', 'is_featured', 'category', 'is_digital', 
        'requires_shipping', 'created_at', 'updated_at'
    ]
    search_fields = ['name', 'sku', 'description', 'brand', 'model']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['status', 'is_featured']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category')
        }),
        ('Pricing & Inventory', {
            'fields': (
                ('price', 'compare_price', 'cost_price'),
                ('stock_quantity', 'min_stock_level'),
                'sku'
            )
        }),
        ('Product Details', {
            'fields': (
                ('brand', 'model'),
                ('weight', 'dimensions'),
                ('requires_shipping', 'is_digital')
            )
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',),
            'description': 'Automatically managed fields'
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [ProductImageInline, ProductVariantInline]
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
        models.CharField: {'widget': TextInput(attrs={'size': '60'})},
    }
    
    def price_display(self, obj):
        """Display price with discount info"""
        if obj.is_on_sale:
            return format_html(
                '<span style="color: #d63384; font-weight: bold;">${}</span><br>'
                '<span style="text-decoration: line-through; color: #666; font-size: 0.9em;">${}</span>',
                obj.price, obj.compare_price
            )
        return f"${obj.price}"
    price_display.short_description = 'Price'
    
    def stock_info(self, obj):
        """Display stock information with alerts"""
        if obj.stock_quantity == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">Out of Stock</span>'
            )
        elif obj.is_low_stock:
            return format_html(
                '<span style="color: #fd7e14; font-weight: bold;">{} (Low Stock)</span>',
                obj.stock_quantity
            )
        else:
            return format_html(
                '<span style="color: #198754;">{}</span>',
                obj.stock_quantity
            )
    stock_info.short_description = 'Stock'
    
    def rating_display(self, obj):
        """Display rating with review count"""
        avg_rating = obj.average_rating
        review_count = obj.review_count
        if avg_rating > 0:
            stars = "★" * int(avg_rating) + "☆" * (5 - int(avg_rating))
            return format_html(
                '<span title="{} stars">{}</span><br>'
                '<small>({} reviews)</small>',
                avg_rating, stars, review_count
            )
        return "No reviews"
    rating_display.short_description = 'Rating'
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by and updated_by"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related(
            'category', 'created_by', 'updated_by'
        ).prefetch_related('images', 'reviews')
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']
    
    def make_active(self, request, queryset):
        """Bulk action to make products active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} products marked as active.')
    make_active.short_description = "Mark selected products as active"
    
    def make_inactive(self, request, queryset):
        """Bulk action to make products inactive"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} products marked as inactive.')
    make_inactive.short_description = "Mark selected products as inactive"
    
    def make_featured(self, request, queryset):
        """Bulk action to feature products"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products marked as featured.')
    make_featured.short_description = "Mark selected products as featured"
    
    def remove_featured(self, request, queryset):
        """Bulk action to remove featured status"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} products removed from featured.')
    remove_featured.short_description = "Remove featured status from selected products"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Admin interface for managing product images separately.
    """
    list_display = ['product', 'image_preview', 'alt_text', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_primary']
    
    def image_preview(self, obj):
        """Show thumbnail preview"""
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Admin interface for managing product variants separately.
    """
    list_display = ['product', 'name', 'sku', 'price_adjustment', 'stock', 'is_active']
    list_filter = ['is_active', 'product__category']
    search_fields = ['product__name', 'name', 'sku']
    list_editable = ['price_adjustment', 'stock', 'is_active']


# Register the Category admin
admin.site.register(Category, CategoryAdmin)
