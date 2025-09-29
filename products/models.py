from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from PIL import Image
import os

User = get_user_model()

class Category(models.Model):
    """
    Product Category model with hierarchical support for subcategories.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Order for displaying categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def is_parent(self):
        """Check if this category has subcategories"""
        return self.subcategories.exists()
    
    @property
    def level(self):
        """Get the level of the category in the hierarchy"""
        if not self.parent:
            return 0
        return self.parent.level + 1
    
    def get_full_path(self):
        """Get the full path of the category including parent categories"""
        if not self.parent:
            return self.name
        return f"{self.parent.get_full_path()} > {self.name}"
    
    def get_children(self):
        """Get all direct children categories"""
        return self.subcategories.filter(is_active=True).order_by('sort_order', 'name')
    
    def get_all_children(self):
        """Get all descendant categories recursively"""
        children = []
        for child in self.get_children():
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def __str__(self):
        return self.get_full_path()
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        unique_together = ['name', 'parent']

class Product(models.Model):
    """
    Product model for motorcycle accessories and gear.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                       help_text="Original price for showing discounts")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                    help_text="Cost price for profit calculations")
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=5, 
                                                 help_text="Minimum stock level for alerts")
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                help_text="Weight in kilograms")
    dimensions = models.CharField(max_length=100, blank=True, null=True,
                                 help_text="Dimensions in format: L x W x H (cm)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    requires_shipping = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=150, blank=True, null=True)
    meta_description = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='created_products')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='updated_products')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        if not self.sku:
            # Generate SKU based on category and product name
            category_prefix = self.category.name[:3].upper()
            name_prefix = ''.join([c for c in self.name.upper() if c.isalnum()])[:6]
            base_sku = f"{category_prefix}-{name_prefix}"
            sku = base_sku
            counter = 1
            while Product.objects.filter(sku=sku).exists():
                sku = f"{base_sku}-{counter:03d}"
                counter += 1
            self.sku = sku
        
        super().save(*args, **kwargs)
    
    @property
    def is_on_sale(self):
        """Check if product is on sale"""
        return self.compare_price and self.compare_price > self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.is_on_sale:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews:
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0
    
    @property
    def review_count(self):
        """Get total number of approved reviews"""
        return self.reviews.filter(is_approved=True).count()
    
    def get_main_image(self):
        """Get the main product image"""
        main_image = self.images.filter(is_primary=True).first()
        if main_image:
            return main_image
        return self.images.first()
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['sku']),
        ]

class ProductImage(models.Model):
    """
    Product Image model for storing multiple images per product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).update(is_primary=False)
        
        super().save(*args, **kwargs)
        
        # Resize image for optimization
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"
    
    class Meta:
        db_table = 'product_images'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['-is_primary', 'created_at']

class ProductVariant(models.Model):
    """
    Product Variant model for storing different variants of a product (e.g., size, color).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)  # e.g., "Red - Large"
    sku = models.CharField(max_length=50, unique=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict)  # e.g., {"color": "red", "size": "large"}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def final_price(self):
        """Calculate final price including adjustments"""
        return self.product.price + self.price_adjustment
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        unique_together = ['product', 'name']
