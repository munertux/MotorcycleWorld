from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from products.serializers import ProductListSerializer, ProductVariantSerializer

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items.
    """
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    unit_price = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_id',
            'quantity', 'unit_price', 'subtotal', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate_quantity(self, value):
        """Validate that quantity doesn't exceed stock"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value
    
    def validate(self, attrs):
        """Validate stock availability"""
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')
        quantity = attrs.get('quantity', 1)
        
        # Import here to avoid circular imports
        from products.models import Product, ProductVariant
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        
        if not product.is_active:
            raise serializers.ValidationError("Product is not available.")
        
        # Check stock based on variant or product
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
                if not variant.is_active:
                    raise serializers.ValidationError("Product variant is not available.")
                if variant.stock < quantity:
                    raise serializers.ValidationError(
                        f"Only {variant.stock} items available in stock."
                    )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found.")
        else:
            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Only {product.stock} items available in stock."
                )
        
        return attrs

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for shopping cart.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'total_price',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items.
    """
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'product_sku', 'variant_name',
            'quantity', 'unit_price', 'total_price'
        ]

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for order status history.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'status', 'status_display', 'notes',
            'created_by_name', 'created_at'
        ]

class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for order list view.
    """
    customer_name = serializers.CharField(source='user.username', read_only=True)
    order_number = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'status', 'status_display',
            'payment_method', 'payment_method_display', 'total_amount',
            'item_count', 'created_at', 'updated_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()

class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for order detail view.
    """
    customer_name = serializers.CharField(source='user.username', read_only=True)
    customer_email = serializers.CharField(source='user.email', read_only=True)
    order_number = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'status', 'status_display', 'payment_method', 'payment_method_display',
            'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount',
            'shipping_name', 'shipping_email', 'shipping_phone', 'shipping_address',
            'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country',
            'tracking_number', 'notes', 'items', 'status_history',
            'created_at', 'updated_at', 'shipped_at', 'delivered_at'
        ]

class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders.
    """
    class Meta:
        model = Order
        fields = [
            'payment_method', 'shipping_name', 'shipping_email', 'shipping_phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country', 'notes'
        ]
    
    def validate(self, attrs):
        """Validate that user has items in cart"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                if not cart.items.exists():
                    raise serializers.ValidationError("Cart is empty.")
            except Cart.DoesNotExist:
                raise serializers.ValidationError("Cart not found.")
        return attrs

class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating orders (admin only).
    """
    class Meta:
        model = Order
        fields = [
            'status', 'tracking_number', 'notes',
            'shipped_at', 'delivered_at'
        ]
    
    def update(self, instance, validated_data):
        """Update order and create status history entry"""
        request = self.context.get('request')
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Update the order
        order = super().update(instance, validated_data)
        
        # Create status history entry if status changed
        if old_status != new_status:
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                notes=f"Status changed from {old_status} to {new_status}",
                created_by=request.user if request else None
            )
        
        return order

class CheckoutSerializer(serializers.Serializer):
    """
    Serializer for checkout process.
    """
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_CHOICES)
    shipping_name = serializers.CharField(max_length=100)
    shipping_email = serializers.EmailField()
    shipping_phone = serializers.CharField(max_length=20)
    shipping_address = serializers.CharField()
    shipping_city = serializers.CharField(max_length=100)
    shipping_state = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20)
    shipping_country = serializers.CharField(max_length=100, default='Country')
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate checkout data"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                if not cart.items.exists():
                    raise serializers.ValidationError("Cart is empty.")
                
                # Validate stock for all items
                for item in cart.items.all():
                    if item.variant:
                        if item.variant.stock < item.quantity:
                            raise serializers.ValidationError(
                                f"Insufficient stock for {item.product.name} - {item.variant.name}"
                            )
                    else:
                        if item.product.stock < item.quantity:
                            raise serializers.ValidationError(
                                f"Insufficient stock for {item.product.name}"
                            )
            except Cart.DoesNotExist:
                raise serializers.ValidationError("Cart not found.")
        
        return attrs
