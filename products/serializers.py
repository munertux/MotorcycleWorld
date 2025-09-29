from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model with hierarchy support.
    """
    product_count = serializers.IntegerField(read_only=True)
    level = serializers.ReadOnlyField()
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image', 'parent',
            'is_active', 'sort_order', 'created_at', 'updated_at',
            'product_count', 'level', 'full_path', 'children'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """Get immediate children categories"""
        if hasattr(obj, 'prefetched_children'):
            children = obj.prefetched_children
        else:
            children = obj.get_children()
        
        return CategorySerializer(children, many=True, context=self.context).data
    
    def validate_parent(self, value):
        """Validate that parent category doesn't create circular reference"""
        if value:
            # Check if setting this parent would create a circular reference
            current_category = self.instance
            if current_category:
                parent = value
                while parent:
                    if parent == current_category:
                        raise serializers.ValidationError(
                            "Cannot set parent category that would create a circular reference."
                        )
                    parent = parent.parent
        return value


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for complete category tree structure.
    """
    product_count = serializers.IntegerField(read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image',
            'sort_order', 'product_count', 'children'
        ]
    
    def get_children(self, obj):
        """Recursively get all children categories"""
        children = obj.subcategories.filter(is_active=True).order_by('sort_order', 'name')
        return CategoryTreeSerializer(children, many=True, context=self.context).data

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductImage model.
    """
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'alt_text', 'is_primary',
            'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']
    
    def validate(self, data):
        """Ensure only one main image per product"""
        if data.get('is_primary', False):
            product = data.get('product') or (self.instance.product if self.instance else None)
            if product:
                existing_main = ProductImage.objects.filter(
                    product=product, is_primary=True
                ).exclude(id=self.instance.id if self.instance else None)
                
                if existing_main.exists():
                    # Auto-remove main status from other images
                    existing_main.update(is_primary=False)
        
        return data


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductVariant model.
    """
    final_price = serializers.SerializerMethodField()
    final_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'name', 'value', 'price_adjustment',
            'stock_adjustment', 'sku_suffix', 'is_active',
            'final_price', 'final_stock'
        ]
    
    def get_final_price(self, obj):
        """Calculate final price with adjustment"""
        base_price = obj.product.price
        return base_price + (obj.price_adjustment or 0)
    
    def get_final_stock(self, obj):
        """Calculate final stock with adjustment"""
        base_stock = obj.product.stock_quantity
        return max(0, base_stock + (obj.stock_adjustment or 0))


class ProductSerializer(serializers.ModelSerializer):
    """
    Basic serializer for Product listing.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    main_image = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'category', 'category_id',
            'brand', 'model', 'sku', 'price', 'compare_price', 'stock_quantity',
            'status', 'is_featured', 'is_digital', 'requires_shipping',
            'main_image', 'avg_rating', 'review_count', 'is_on_sale',
            'discount_percentage', 'is_in_stock', 'is_low_stock', 'created_at'
        ]
        read_only_fields = ['slug', 'sku', 'created_at']
    
    def get_main_image(self, obj):
        """Get main product image URL"""
        main_image = obj.get_main_image()
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None
    
    def get_avg_rating(self, obj):
        """Get average rating"""
        return obj.average_rating
    
    def get_review_count(self, obj):
        """Get review count"""
        return obj.review_count
    
    def validate_category_id(self, value):
        """Validate category exists and is active"""
        try:
            category = Category.objects.get(id=value)
            if not category.is_active:
                raise serializers.ValidationError("Selected category is not active.")
            return value
        except Category.DoesNotExist:
            raise serializers.ValidationError("Invalid category selected.")
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_stock_quantity(self, value):
        """Validate stock quantity is not negative"""
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value
    
    def validate(self, data):
        """Additional validation for product data"""
        # Validate compare_price is higher than price if set
        compare_price = data.get('compare_price')
        price = data.get('price')
        
        if compare_price and price and compare_price <= price:
            raise serializers.ValidationError({
                'compare_price': 'Compare price must be higher than regular price.'
            })
        
        # Validate cost_price is not higher than price
        cost_price = data.get('cost_price')
        if cost_price and price and cost_price > price:
            raise serializers.ValidationError({
                'cost_price': 'Cost price should not be higher than selling price.'
            })
        
        return data


class ProductDetailSerializer(ProductSerializer):
    """
    Detailed serializer for Product with all related data.
    """
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_path = serializers.CharField(source='category.get_full_path', read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + [
            'description', 'cost_price', 'min_stock_level', 'weight',
            'dimensions', 'meta_title', 'meta_description', 'updated_at',
            'created_by', 'updated_by', 'images', 'variants', 'category_path'
        ]
        read_only_fields = ProductSerializer.Meta.read_only_fields + [
            'created_by', 'updated_by', 'updated_at'
        ]
    
    def to_representation(self, instance):
        """Customize the representation"""
        data = super().to_representation(instance)
        
        # Add computed fields
        data['total_variants'] = instance.variants.filter(is_active=True).count()
        data['total_images'] = instance.images.count()
        
        # Add stock status
        if instance.stock_quantity == 0:
            data['stock_status'] = 'out_of_stock'
        elif instance.is_low_stock:
            data['stock_status'] = 'low_stock'
        else:
            data['stock_status'] = 'in_stock'
        
        return data
