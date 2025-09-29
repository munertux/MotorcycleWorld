from django import forms
from .models import Product, Category, ProductImage, ProductVariant

class ProductForm(forms.ModelForm):
    """Formulario para crear/editar productos"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category',
            'brand', 'model', 'price', 'compare_price', 'cost_price',
            'stock_quantity', 'min_stock_level', 'weight', 'dimensions',
            'status', 'is_featured', 'is_digital', 'requires_shipping',
            'meta_title', 'meta_description'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del producto'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción corta para listados'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Marca del producto'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Modelo del producto'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'compare_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio antes del descuento (opcional)'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio de costo (opcional)'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cantidad en inventario'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nivel mínimo de stock'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Peso en kg'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 30 x 20 x 15 cm'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título para SEO (opcional)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción para SEO (opcional)'
            }),
        }

class CategoryForm(forms.ModelForm):
    """Formulario para crear/editar categorías"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'sort_order', 'is_active']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Selecciona categoría padre (opcional)'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Orden de visualización'
            }),
        }

class ProductImageForm(forms.ModelForm):
    """Formulario para subir imágenes de productos"""
    
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']
        
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Texto alternativo para la imagen'
            }),
        }
