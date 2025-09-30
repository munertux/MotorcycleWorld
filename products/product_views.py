from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from products.models import Product, Category
from reviews.models import Review, ReviewSummary
from services.ai_review_service import ai_review_service
import json

def product_detail_view(request, product_id):
    """Vista para mostrar el detalle de un producto con reseñas"""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'variants'),
        id=product_id,
        status='active'
    )
    
    # Obtener reseñas del producto
    reviews = Review.objects.filter(product=product).select_related('user').order_by('-created_at')
    
    # Paginación de reseñas
    paginator = Paginator(reviews, 5)  # 5 reseñas por página
    page_number = request.GET.get('page')
    reviews_page = paginator.get_page(page_number)
    
    # Estadísticas de reseñas
    review_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Distribución de calificaciones
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = reviews.filter(rating=i).count()
    
    # Productos relacionados (misma categoría)
    related_products = Product.objects.filter(
        category=product.category,
        status='active'
    ).exclude(id=product.id)[:6]
    
    # Obtener resumen de IA si existe
    review_summary = ReviewSummary.objects.filter(product=product).first()

    context = {
        'product': product,
        'reviews': reviews_page,
        'review_stats': review_stats,
        'rating_distribution': rating_distribution,
        'related_products': related_products,
        'user_has_reviewed': False,
        'review_summary': review_summary,
    }
    # Categorías principales para el header compartido
    main_categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related('subcategories').annotate(
        product_count=Count('products', filter=Q(products__status='active'))
    ).order_by('sort_order', 'name')
    context['categories'] = main_categories
    
    # Verificar si el usuario ya ha reseñado este producto
    if request.user.is_authenticated:
        context['user_has_reviewed'] = reviews.filter(user=request.user).exists()
    
    return render(request, 'product_detail.html', context)

@login_required
@require_http_methods(["POST"])
def add_review(request, product_id):
    """Vista para agregar una reseña a un producto"""
    try:
        product = get_object_or_404(Product, id=product_id, status='active')
        
        # Verificar si ya tiene una reseña
        if Review.objects.filter(product=product, user=request.user).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya has reseñado este producto'
            })
        
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()
        
        # Validaciones
        if not (1 <= rating <= 5):
            return JsonResponse({
                'success': False,
                'error': 'La calificación debe estar entre 1 y 5'
            })
        
        if len(comment) < 10:
            return JsonResponse({
                'success': False,
                'error': 'El comentario debe tener al menos 10 caracteres'
            })
        
        # Crear la reseña
        review = Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        # Actualizar/resumir con IA (mejor esfuerzo)
        try:
            ai_review_service.update_product_summary(product.id)
        except Exception:
            pass
        
        return JsonResponse({
            'success': True,
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user_name': review.user.get_full_name() or review.user.username,
                'created_at': review.created_at.strftime('%d de %B de %Y')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al agregar la reseña'
        })

@require_http_methods(["GET"])
def get_product_reviews(request, product_id):
    """Vista para obtener reseñas de un producto via AJAX"""
    try:
        product = get_object_or_404(Product, id=product_id, status='active')
        page_number = request.GET.get('page', 1)
        
        reviews = Review.objects.filter(product=product).select_related('user').order_by('-created_at')
        paginator = Paginator(reviews, 5)
        reviews_page = paginator.get_page(page_number)
        
        reviews_data = []
        for review in reviews_page:
            reviews_data.append({
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user_name': review.user.get_full_name() or review.user.username,
                'created_at': review.created_at.strftime('%d de %B de %Y')
            })
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'has_next': reviews_page.has_next(),
            'has_previous': reviews_page.has_previous(),
            'current_page': reviews_page.number,
            'total_pages': paginator.num_pages
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error al cargar las reseñas'
        })
