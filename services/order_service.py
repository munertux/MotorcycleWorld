"""
Order Service for handling order creation and management.

This service contains business logic for order processing, cart management,
and inventory updates.
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from orders.models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from products.models import Product, ProductVariant

logger = logging.getLogger(__name__)
User = get_user_model()

class OrderService:
    """
    Service for handling order-related business logic.
    """
    
    @staticmethod
    def get_or_create_cart(user: User) -> Cart:
        """
        Get or create a cart for the user.
        
        Args:
            user: User instance
            
        Returns:
            Cart: User's cart
        """
        cart, created = Cart.objects.get_or_create(user=user)
        if created:
            logger.info(f"Created new cart for user {user.username}")
        return cart
    
    @staticmethod
    def add_to_cart(user: User, product_id: int, variant_id: int = None, 
                   quantity: int = 1) -> dict:
        """
        Add a product to user's cart.
        
        Args:
            user: User instance
            product_id: ID of the product to add
            variant_id: ID of the product variant (optional)
            quantity: Quantity to add
            
        Returns:
            dict: Result with success status and message
        """
        try:
            with transaction.atomic():
                # Get or create cart
                cart = OrderService.get_or_create_cart(user)
                
                # Get product
                try:
                    product = Product.objects.get(id=product_id, is_active=True)
                except Product.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'Product not found or inactive'
                    }
                
                # Get variant if specified
                variant = None
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(
                            id=variant_id, 
                            product=product, 
                            is_active=True
                        )
                    except ProductVariant.DoesNotExist:
                        return {
                            'success': False,
                            'message': 'Product variant not found or inactive'
                        }
                
                # Check stock
                available_stock = variant.stock if variant else product.stock
                if available_stock < quantity:
                    return {
                        'success': False,
                        'message': f'Only {available_stock} items available in stock'
                    }
                
                # Check if item already exists in cart
                existing_item = CartItem.objects.filter(
                    cart=cart,
                    product=product,
                    variant=variant
                ).first()
                
                if existing_item:
                    # Update quantity
                    new_quantity = existing_item.quantity + quantity
                    if available_stock < new_quantity:
                        return {
                            'success': False,
                            'message': f'Cannot add {quantity} more items. Only {available_stock - existing_item.quantity} more available'
                        }
                    existing_item.quantity = new_quantity
                    existing_item.save()
                    action = 'updated'
                else:
                    # Create new cart item
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        variant=variant,
                        quantity=quantity
                    )
                    action = 'added'
                
                logger.info(f"Product {product.name} {action} to cart for user {user.username}")
                return {
                    'success': True,
                    'message': f'Product {action} to cart successfully'
                }
                
        except Exception as e:
            logger.error(f"Error adding product to cart: {str(e)}")
            return {
                'success': False,
                'message': f'Error adding product to cart: {str(e)}'
            }
    
    @staticmethod
    def update_cart_item(user: User, cart_item_id: int, quantity: int) -> dict:
        """
        Update quantity of a cart item.
        
        Args:
            user: User instance
            cart_item_id: ID of the cart item to update
            quantity: New quantity
            
        Returns:
            dict: Result with success status and message
        """
        try:
            with transaction.atomic():
                cart = OrderService.get_or_create_cart(user)
                
                try:
                    cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
                except CartItem.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'Cart item not found'
                    }
                
                if quantity <= 0:
                    cart_item.delete()
                    return {
                        'success': True,
                        'message': 'Item removed from cart'
                    }
                
                # Check stock
                available_stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
                if available_stock < quantity:
                    return {
                        'success': False,
                        'message': f'Only {available_stock} items available in stock'
                    }
                
                cart_item.quantity = quantity
                cart_item.save()
                
                return {
                    'success': True,
                    'message': 'Cart item updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating cart item: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating cart item: {str(e)}'
            }
    
    @staticmethod
    def remove_from_cart(user: User, cart_item_id: int) -> dict:
        """
        Remove an item from the cart.
        
        Args:
            user: User instance
            cart_item_id: ID of the cart item to remove
            
        Returns:
            dict: Result with success status and message
        """
        try:
            cart = OrderService.get_or_create_cart(user)
            
            try:
                cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
                cart_item.delete()
                
                return {
                    'success': True,
                    'message': 'Item removed from cart successfully'
                }
            except CartItem.DoesNotExist:
                return {
                    'success': False,
                    'message': 'Cart item not found'
                }
                
        except Exception as e:
            logger.error(f"Error removing cart item: {str(e)}")
            return {
                'success': False,
                'message': f'Error removing cart item: {str(e)}'
            }
    
    @staticmethod
    def clear_cart(user: User) -> dict:
        """
        Clear all items from user's cart.
        
        Args:
            user: User instance
            
        Returns:
            dict: Result with success status and message
        """
        try:
            cart = OrderService.get_or_create_cart(user)
            cart.items.all().delete()
            
            return {
                'success': True,
                'message': 'Cart cleared successfully'
            }
            
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            return {
                'success': False,
                'message': f'Error clearing cart: {str(e)}'
            }
    
    @staticmethod
    def create_order(user: User, order_data: dict) -> dict:
        """
        Create an order from user's cart.
        
        Args:
            user: User instance
            order_data: Dictionary containing order information
            
        Returns:
            dict: Result with success status, message, and order data
        """
        try:
            with transaction.atomic():
                # Get user's cart
                try:
                    cart = Cart.objects.get(user=user)
                except Cart.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'Cart not found'
                    }
                
                if not cart.items.exists():
                    return {
                        'success': False,
                        'message': 'Cart is empty'
                    }
                
                # Validate stock for all items
                for cart_item in cart.items.all():
                    available_stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
                    if available_stock < cart_item.quantity:
                        return {
                            'success': False,
                            'message': f'Insufficient stock for {cart_item.product.name}'
                        }
                
                # Calculate totals
                subtotal = cart.total_price
                shipping_cost = OrderService._calculate_shipping_cost(subtotal)
                tax_amount = OrderService._calculate_tax_amount(subtotal)
                discount_amount = Decimal('0.00')  # Could be implemented later
                total_amount = subtotal + shipping_cost + tax_amount - discount_amount
                
                # Create order
                order = Order.objects.create(
                    user=user,
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    total_amount=total_amount,
                    **order_data
                )
                
                # Create order items and update stock
                for cart_item in cart.items.all():
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price
                    )
                    
                    # Update stock
                    if cart_item.variant:
                        cart_item.variant.stock -= cart_item.quantity
                        cart_item.variant.save()
                    else:
                        cart_item.product.stock -= cart_item.quantity
                        cart_item.product.save()
                
                # Create initial status history
                OrderStatusHistory.objects.create(
                    order=order,
                    status='pending',
                    notes='Order created',
                    created_by=user
                )
                
                # Clear cart
                cart.items.all().delete()
                
                logger.info(f"Order {order.order_number} created for user {user.username}")
                
                return {
                    'success': True,
                    'message': 'Order created successfully',
                    'order': order
                }
                
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating order: {str(e)}'
            }
    
    @staticmethod
    def _calculate_shipping_cost(subtotal: Decimal) -> Decimal:
        """
        Calculate shipping cost based on subtotal.
        
        Args:
            subtotal: Order subtotal
            
        Returns:
            Decimal: Shipping cost
        """
        # Simple shipping calculation - free shipping over $100
        if subtotal >= Decimal('100.00'):
            return Decimal('0.00')
        else:
            return Decimal('10.00')  # Flat rate shipping
    
    @staticmethod
    def _calculate_tax_amount(subtotal: Decimal) -> Decimal:
        """
        Calculate tax amount based on subtotal.
        
        Args:
            subtotal: Order subtotal
            
        Returns:
            Decimal: Tax amount
        """
        # Simple tax calculation - 8% tax rate
        tax_rate = Decimal('0.08')
        return subtotal * tax_rate
    
    @staticmethod
    def update_order_status(order_id: str, new_status: str, notes: str = None, 
                           updated_by: User = None) -> dict:
        """
        Update order status and create history entry.
        
        Args:
            order_id: Order ID
            new_status: New status value
            notes: Optional notes
            updated_by: User making the update
            
        Returns:
            dict: Result with success status and message
        """
        try:
            with transaction.atomic():
                try:
                    order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'Order not found'
                    }
                
                old_status = order.status
                order.status = new_status
                
                # Update timestamps based on status
                if new_status == 'shipped' and not order.shipped_at:
                    from django.utils import timezone
                    order.shipped_at = timezone.now()
                elif new_status == 'delivered' and not order.delivered_at:
                    from django.utils import timezone
                    order.delivered_at = timezone.now()
                
                order.save()
                
                # Create status history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status=new_status,
                    notes=notes or f"Status changed from {old_status} to {new_status}",
                    created_by=updated_by
                )
                
                logger.info(f"Order {order.order_number} status updated to {new_status}")
                
                return {
                    'success': True,
                    'message': 'Order status updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating order status: {str(e)}'
            }


# Service instance
order_service = OrderService()
