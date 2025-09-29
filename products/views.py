from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, F
from django_filters import rest_framework as django_filters
from .models import Product, Category, ProductImage, ProductVariant
from .serializers import (
    ProductSerializer, ProductDetailSerializer, CategorySerializer,
    CategoryTreeSerializer, ProductImageSerializer, ProductVariantSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductFilter(django_filters.FilterSet):
    """Advanced filtering for products"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    category_tree = django_filters.CharFilter(method='filter_category_tree')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    brand = django_filters.CharFilter(lookup_expr='icontains')
    is_featured = django_filters.BooleanFilter()
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    on_sale = django_filters.BooleanFilter(method='filter_on_sale')
    
    class Meta:
        model = Product
        fields = ['status', 'is_featured', 'is_digital', 'requires_shipping']
    
    def filter_category_tree(self, queryset, name, value):
        """Filter by category and all its subcategories"""
        try:
            category = Category.objects.get(slug=value)
            # Get all subcategories
            subcategories = category.get_all_children()
            category_ids = [category.id] + [cat.id for cat in subcategories]
            return queryset.filter(category__id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock"""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)
    
    def filter_on_sale(self, queryset, name, value):
        """Filter products that are on sale"""
        if value:
            return queryset.filter(compare_price__gt=F('price'))
        return queryset.filter(Q(compare_price__isnull=True) | Q(compare_price__lte=F('price')))


class CategoryFilter(django_filters.FilterSet):
    """Filtering for categories"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    is_parent = django_filters.BooleanFilter(method='filter_is_parent')
    
    class Meta:
        model = Category
        fields = ['is_active']
    
    def filter_is_parent(self, queryset, name, value):
        """Filter categories that have or don't have subcategories"""
        if value:
            return queryset.filter(subcategories__isnull=False).distinct()
        return queryset.filter(subcategories__isnull=True)


class ProductListView(generics.ListCreateAPIView):
    """
    List all products or create a new product.
    Supports filtering, searching, and pagination.
    """
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'brand', 'model', 'sku']
    ordering_fields = ['name', 'price', 'created_at', 'stock_quantity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Optimized queryset with related data"""
        return Product.objects.select_related('category', 'created_by').prefetch_related(
            'images', 'variants', 'reviews'
        )
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.request.method in ['POST']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        """Set created_by when creating a product"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product.
    """
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Optimized queryset with all related data"""
        return Product.objects.select_related('category', 'created_by', 'updated_by').prefetch_related(
            'images', 'variants', 'reviews__user'
        )
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def perform_update(self, serializer):
        """Set updated_by when updating a product"""
        serializer.save(updated_by=self.request.user)


class CategoryListView(generics.ListCreateAPIView):
    """
    List all categories or create a new category.
    Supports hierarchical display and filtering.
    """
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']
    
    def get_queryset(self):
        """Return categories with product counts"""
        return Category.objects.select_related('parent').prefetch_related('subcategories').annotate(
            product_count=Count('products', filter=Q(products__status='active'))
        )
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.request.method in ['POST']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a category.
    """
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Optimized queryset with related data"""
        return Category.objects.select_related('parent').prefetch_related(
            'subcategories', 'products'
        ).annotate(
            product_count=Count('products', filter=Q(products__status='active'))
        )
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class CategoryTreeView(generics.ListAPIView):
    """
    Get complete category hierarchy tree.
    """
    serializer_class = CategoryTreeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination for tree view
    
    def get_queryset(self):
        """Return only parent categories (will include children via serializer)"""
        return Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related(
            'subcategories', 'subcategories__subcategories'
        ).annotate(
            product_count=Count('products', filter=Q(products__status='active'))
        ).order_by('sort_order', 'name')


class ProductImageListView(generics.ListCreateAPIView):
    """
    Manage product images.
    """
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter by product if specified"""
        queryset = ProductImage.objects.select_related('product')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset.order_by('sort_order')


class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Manage individual product image.
    """
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = ProductImage.objects.all()


class ProductVariantListView(generics.ListCreateAPIView):
    """
    Manage product variants.
    """
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter by product if specified"""
        queryset = ProductVariant.objects.select_related('product')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset.order_by('name', 'value')


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Manage individual product variant.
    """
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = ProductVariant.objects.all()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_products(request):
    """Get featured products for homepage"""
    products = Product.objects.filter(
        is_featured=True, 
        status='active'
    ).select_related('category').prefetch_related('images')[:8]
    
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_suggestions(request):
    """Get search suggestions based on query"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return Response({'suggestions': []})
    
    # Get product name suggestions
    product_suggestions = Product.objects.filter(
        name__icontains=query,
        status='active'
    ).values_list('name', flat=True)[:5]
    
    # Get category suggestions
    category_suggestions = Category.objects.filter(
        name__icontains=query,
        is_active=True
    ).values_list('name', flat=True)[:3]
    
    # Get brand suggestions
    brand_suggestions = Product.objects.filter(
        brand__icontains=query,
        status='active'
    ).values_list('brand', flat=True).distinct()[:3]
    
    suggestions = {
        'products': list(product_suggestions),
        'categories': list(category_suggestions),
        'brands': list(brand_suggestions)
    }
    
    return Response({'suggestions': suggestions})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def bulk_update_products(request):
    """Bulk update products"""
    product_ids = request.data.get('product_ids', [])
    updates = request.data.get('updates', {})
    
    if not product_ids or not updates:
        return Response(
            {'error': 'product_ids and updates are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        updated_count = Product.objects.filter(id__in=product_ids).update(**updates)
        return Response({
            'message': f'{updated_count} products updated successfully',
            'updated_count': updated_count
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
