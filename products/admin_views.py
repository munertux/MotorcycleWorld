from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import Product, Category, ProductImage
from .forms import ProductForm, CategoryForm, ProductImageForm
from orders.models import Order


def is_admin(user):
    """Verificar si el usuario es administrador"""
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Panel principal de administración"""
    # Estadísticas básicas
    stats = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(status='active').count(),
        'total_categories': Category.objects.count(),
        'total_orders': Order.objects.count(),
        'low_stock_products': Product.objects.filter(
            stock_quantity__lte=F('min_stock_level')
        ).count(),
    }
    
    # Productos con stock bajo
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level')
    )[:5]
    
    # Productos más populares (por número de órdenes)
    popular_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:5]
    
    context = {
        'stats': stats,
        'low_stock_products': low_stock_products,
        'popular_products': popular_products,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_products_list(request):
    """Lista de productos para administración"""
    products = Product.objects.all().select_related('category')
    
    # Filtros
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(brand__icontains=search) |
            Q(model__icontains=search)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if status:
        products = products.filter(status=status)
    
    # Paginación
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Categorías para el filtro
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
        'current_category': category_id,
        'current_status': status,
    }
    
    return render(request, 'admin/products_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_product_create(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('panel_admin:product_edit', product_id=product.id)
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Crear Producto',
        'action': 'create'
    }
    
    return render(request, 'admin/product_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_product_edit(request, product_id):
    """Editar producto existente"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('panel_admin:product_edit', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    
    # Imágenes del producto
    images = ProductImage.objects.filter(product=product)
    
    context = {
        'form': form,
        'product': product,
        'images': images,
        'title': f'Editar Producto: {product.name}',
        'action': 'edit'
    }
    
    return render(request, 'admin/product_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_product_delete(request, product_id):
    """Eliminar producto"""
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Producto "{product_name}" eliminado.'})
    
    messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
    return redirect('panel_admin:products_list')


@login_required
@user_passes_test(is_admin)
def admin_categories_list(request):
    """Lista de categorías para administración"""
    categories = Category.objects.all().select_related('parent')
    
    # Filtros
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    
    context = {
        'categories': categories,
        'search': search,
    }
    
    return render(request, 'admin/categories_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_category_create(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
            return redirect('panel_admin:categories_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Crear Categoría',
        'action': 'create'
    }
    
    return render(request, 'admin/category_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_category_edit(request, category_id):
    """Editar categoría existente"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" actualizada exitosamente.')
            return redirect('panel_admin:categories_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'Editar Categoría: {category.name}',
        'action': 'edit'
    }
    
    return render(request, 'admin/category_form.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_category_delete(request, category_id):
    """Eliminar categoría"""
    category = get_object_or_404(Category, id=category_id)
    
    # Verificar si tiene productos asociados
    if category.products.exists():
        message = f'No se puede eliminar la categoría "{category.name}" porque tiene productos asociados.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message})
        messages.error(request, message)
        return redirect('panel_admin:categories_list')
    
    category_name = category.name
    category.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Categoría "{category_name}" eliminada.'})
    
    messages.success(request, f'Categoría "{category_name}" eliminada exitosamente.')
    return redirect('panel_admin:categories_list')


@login_required
@user_passes_test(is_admin)
def admin_product_images(request, product_id):
    """Gestionar imágenes de producto"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.product = product
            image.save()
            messages.success(request, 'Imagen agregada exitosamente.')
            return redirect('panel_admin:product_images', product_id=product.id)
    else:
        form = ProductImageForm()
    
    images = ProductImage.objects.filter(product=product)
    
    context = {
        'product': product,
        'images': images,
        'form': form,
    }
    
    return render(request, 'admin/product_images.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_image_delete(request, image_id):
    """Eliminar imagen de producto"""
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id
    image.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Imagen eliminada.'})
    
    messages.success(request, 'Imagen eliminada exitosamente.')
    return redirect('panel_admin:product_images', product_id=product_id)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_image_set_primary(request, image_id):
    """Establecer imagen como principal"""
    image = get_object_or_404(ProductImage, id=image_id)
    
    # Quitar primary de todas las imágenes del producto
    ProductImage.objects.filter(product=image.product).update(is_primary=False)
    
    # Establecer esta imagen como principal
    image.is_primary = True
    image.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Imagen establecida como principal.'})
    
    messages.success(request, 'Imagen establecida como principal.')
    return redirect('panel_admin:product_images', product_id=image.product.id)

@login_required
@user_passes_test(is_admin)
def admin_product_create_alt(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        # Procesar datos del formulario
        data = request.POST.dict()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        
        try:
            product = Product.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                short_description=data.get('short_description'),
                category_id=data.get('category'),
                brand=data.get('brand'),
                model=data.get('model'),
                price=data.get('price'),
                compare_price=data.get('compare_price') or None,
                stock_quantity=data.get('stock_quantity', 0),
                status=data.get('status', 'draft'),
                is_featured=data.get('is_featured') == 'on',
                created_by=request.user,
                updated_by=request.user
            )
            
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    return render(request, 'admin/product_form.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def admin_product_edit_alt(request, slug):
    """Editar producto existente"""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        data = request.POST.dict()
        
        try:
            product.name = data.get('name')
            product.description = data.get('description')
            product.short_description = data.get('short_description')
            product.category_id = data.get('category')
            product.brand = data.get('brand')
            product.model = data.get('model')
            product.price = data.get('price')
            product.compare_price = data.get('compare_price') or None
            product.stock_quantity = data.get('stock_quantity', 0)
            product.status = data.get('status', 'draft')
            product.is_featured = data.get('is_featured') == 'on'
            product.updated_by = request.user
            product.save()
            
            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar producto: {str(e)}')
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    context = {
        'product': product,
        'categories': categories,
        'is_edit': True
    }
    return render(request, 'admin/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_categories_alt(request):
    """Gestión de categorías"""
    categories = Category.objects.all().select_related('parent').order_by('parent__name', 'sort_order', 'name')
    
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    
    context = {
        'categories': categories,
        'search': search,
    }
    return render(request, 'admin/categories.html', context)

@login_required
@user_passes_test(is_admin)
def admin_category_create_alt(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        data = request.POST.dict()
        
        try:
            category = Category.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                parent_id=data.get('parent') or None,
                sort_order=data.get('sort_order', 0),
                is_active=data.get('is_active') == 'on'
            )
            
            messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
            return redirect('admin_categories')
            
        except Exception as e:
            messages.error(request, f'Error al crear categoría: {str(e)}')
    
    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    return render(request, 'admin/category_form.html', {'parent_categories': parent_categories})

@login_required
@user_passes_test(is_admin)
def admin_product_delete_alt(request, slug):
    """Eliminar producto"""
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
    
    return redirect('admin_products')

@login_required
@user_passes_test(is_admin)
def admin_bulk_actions_alt(request):
    """Acciones masivas para productos"""
    if request.method == 'POST':
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')
        
        if not product_ids:
            messages.error(request, 'No se seleccionaron productos.')
            return redirect('admin_products')
        
        products = Product.objects.filter(id__in=product_ids)
        
        if action == 'activate':
            products.update(status='active')
            messages.success(request, f'{len(product_ids)} productos activados.')
        elif action == 'deactivate':
            products.update(status='inactive')
            messages.success(request, f'{len(product_ids)} productos desactivados.')
        elif action == 'feature':
            products.update(is_featured=True)
            messages.success(request, f'{len(product_ids)} productos marcados como destacados.')
        elif action == 'unfeature':
            products.update(is_featured=False)
            messages.success(request, f'{len(product_ids)} productos desmarcados como destacados.')
        elif action == 'delete':
            count = len(product_ids)
            products.delete()
            messages.success(request, f'{count} productos eliminados.')
    
    return redirect('admin_products')
