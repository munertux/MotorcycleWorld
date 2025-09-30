from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.db.models import Count, Q
from .models import Product, Category


class HomeView(TemplateView):
    """Vista principal del sitio con categorías dinámicas"""
    template_name = 'home_ml.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener categorías principales (sin padre) con sus subcategorías
        main_categories = Category.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).prefetch_related(
            'subcategories__products'
        ).annotate(
            product_count=Count('products', filter=Q(products__status='active'))
        ).order_by('sort_order', 'name')
        
        # Anotar conteo de productos para subcategorías
        for category in main_categories:
            for subcategory in category.subcategories.all():
                subcategory.product_count = subcategory.products.filter(status='active').count()
        
        context['categories'] = main_categories
        
        # Productos destacados para mostrar en el home
        featured_products = Product.objects.filter(
            is_featured=True,
            status='active'
        ).select_related('category')[:8]
        
        context['featured_products'] = featured_products
        
        return context


def category_products_view(request, category_slug):
    """Vista para mostrar productos de una categoría específica"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    # Obtener subcategorías si las tiene
    subcategories = category.subcategories.filter(is_active=True)
    
    # Obtener productos de la categoría y sus subcategorías
    category_ids = [category.id]
    if subcategories.exists():
        category_ids.extend(subcategories.values_list('id', flat=True))
    
    products = Product.objects.filter(
        category__id__in=category_ids,
        status='active'
    ).select_related('category').prefetch_related('images')
    
    # Filtros adicionales desde la URL
    min_price = request.GET.get('price_min')
    max_price = request.GET.get('price_max')
    search = request.GET.get('search')
    
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(brand__icontains=search)
        )
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorías principales para la navegación superior (igual que en home)
    main_categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related('subcategories').annotate(
        product_count=Count('products', filter=Q(products__status='active'))
    ).order_by('sort_order', 'name')

    context = {
        'category': category,
        'subcategories': subcategories,
        'products': page_obj,
        'total_products': products.count(),
        'categories': main_categories,
        'current_filters': {
            'price_min': min_price,
            'price_max': max_price,
            'search': search,
        }
    }
    
    return render(request, 'category_products.html', context)
