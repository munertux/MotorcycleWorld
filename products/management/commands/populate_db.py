"""
Management command to populate the database with sample data for Motorcycle World.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, ProductVariant
from orders.models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
# Note: Reviews are only user-generated; do not seed sample reviews
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data for motorcycle accessories'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Create users
        self.create_users()
        
        # Create hierarchical categories
        self.create_categories()
        
        # Create products
        self.create_products()
        
        # Create sample orders
        self.create_sample_orders()
        
        # Do not create fake/sample reviews. Reviews should be real user content.
        
        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))

    def create_users(self):
        self.stdout.write('Creating users...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@motorcycleworld.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(f'Created admin user: admin')

        # Create customer users
        customers_data = [
            {
                'username': 'carlos_rider',
                'email': 'carlos@email.com',
                'password': 'customer123',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'phone': '+57 300 123 4567',
                'address': 'Calle 123 #45-67, Bogotá',
                'date_of_birth': '1985-06-15'
            },
            {
                'username': 'maria_biker',
                'email': 'maria@email.com',
                'password': 'customer123',
                'first_name': 'María',
                'last_name': 'García',
                'phone': '+57 310 234 5678',
                'address': 'Carrera 45 #67-89, Medellín',
                'date_of_birth': '1990-09-22'
            },
            {
                'username': 'andres_moto',
                'email': 'andres@email.com',
                'password': 'customer123',
                'first_name': 'Andrés',
                'last_name': 'López',
                'phone': '+57 320 345 6789',
                'address': 'Avenida 80 #12-34, Cali',
                'date_of_birth': '1988-03-10'
            }
        ]

        for customer_data in customers_data:
            if not User.objects.filter(username=customer_data['username']).exists():
                User.objects.create_user(**customer_data)
                self.stdout.write(f'Created customer: {customer_data["username"]}')

    def create_categories(self):
        self.stdout.write('Creating hierarchical categories...')
        
        # Define hierarchical category structure
        categories_structure = {
            'Cascos': {
                'description': 'Cascos de seguridad para motociclistas',
                'sort_order': 1,
                'children': {
                    'Cascos Integrales': {'description': 'Máxima protección y aerodinámica'},
                    'Cascos Abiertos': {'description': 'Comodidad para ciudad'},
                    'Cascos Modulares': {'description': 'Versatilidad y funcionalidad'},
                    'Cascos Off-Road': {'description': 'Para aventuras todo terreno'}
                }
            },
            'Chaquetas y Protección': {
                'description': 'Equipamiento de protección corporal',
                'sort_order': 2,
                'children': {
                    'Chaquetas de Cuero': {'description': 'Estilo clásico y protección'},
                    'Chaquetas Textiles': {'description': 'Versatilidad y comodidad'},
                    'Chalecos Protectores': {'description': 'Protección adicional'},
                    'Protecciones Individuales': {'description': 'Coderas, rodilleras y más'}
                }
            },
            'Guantes': {
                'description': 'Protección y control para tus manos',
                'sort_order': 3,
                'children': {
                    'Guantes de Verano': {'description': 'Transpirables y ligeros'},
                    'Guantes de Invierno': {'description': 'Cálidos e impermeables'},
                    'Guantes de Carreras': {'description': 'Máximo agarre y protección'},
                    'Guantes Todo Terreno': {'description': 'Para aventuras off-road'}
                }
            },
            'Botas y Calzado': {
                'description': 'Calzado especializado para motociclistas',
                'sort_order': 4,
                'children': {
                    'Botas de Carretera': {'description': 'Comodidad para largos viajes'},
                    'Botas de Ciudad': {'description': 'Estilo urbano y protección'},
                    'Botas Off-Road': {'description': 'Para terrenos difíciles'},
                    'Botas de Lluvia': {'description': 'Impermeables y seguras'}
                }
            },
            'Accesorios': {
                'description': 'Accesorios para mejorar tu experiencia',
                'sort_order': 5,
                'children': {
                    'Comunicación': {'description': 'Intercomunicadores y más'},
                    'Navegación': {'description': 'GPS y soportes'},
                    'Iluminación': {'description': 'Luces adicionales'},
                    'Equipaje': {'description': 'Maletas y bolsos'}
                }
            },
            'Repuestos': {
                'description': 'Repuestos y componentes originales',
                'sort_order': 6,
                'children': {
                    'Filtros': {'description': 'Filtros de aire, aceite y combustible'},
                    'Frenos': {'description': 'Pastillas y discos de freno'},
                    'Neumáticos': {'description': 'Llantas para toda ocasión'},
                    'Lubricantes': {'description': 'Aceites y lubricantes'}
                }
            }
        }

        # Create parent categories and their children
        for parent_name, parent_data in categories_structure.items():
            # Create parent category
            parent_category, created = Category.objects.get_or_create(
                name=parent_name,
                defaults={
                    'description': parent_data['description'],
                    'sort_order': parent_data['sort_order'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created parent category: {parent_name}')
            
            # Create child categories
            for child_name, child_data in parent_data.get('children', {}).items():
                child_category, created = Category.objects.get_or_create(
                    name=child_name,
                    parent=parent_category,
                    defaults={
                        'description': child_data['description'],
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'Created child category: {child_name}')

    def create_products(self):
        self.stdout.write('Creating products...')
        
        # Get admin user for created_by field
        admin_user = User.objects.get(username='admin')
        
        # Sample products by category
        products_data = {
            'Cascos Integrales': [
                {
                    'name': 'Casco AGV K1 Solid',
                    'description': 'Casco integral deportivo con excelente aerodinámica y ventilación. Homologado ECE 22.05.',
                    'short_description': 'Casco integral deportivo AGV con homologación ECE',
                    'brand': 'AGV',
                    'model': 'K1 Solid',
                    'price': Decimal('450000'),
                    'compare_price': Decimal('520000'),
                    'cost_price': Decimal('320000'),
                    'stock_quantity': 25,
                    'weight': Decimal('1.5'),
                    'dimensions': '35 x 25 x 25 cm',
                    'is_featured': True
                },
                {
                    'name': 'Casco Shoei RF-1400',
                    'description': 'Casco integral premium con tecnología avanzada y máximo confort.',
                    'short_description': 'Casco integral premium Shoei de alta gama',
                    'brand': 'Shoei',
                    'model': 'RF-1400',
                    'price': Decimal('850000'),
                    'compare_price': Decimal('950000'),
                    'cost_price': Decimal('600000'),
                    'stock_quantity': 15,
                    'weight': Decimal('1.4'),
                    'dimensions': '35 x 25 x 25 cm',
                    'is_featured': True
                }
            ],
            'Chaquetas de Cuero': [
                {
                    'name': 'Chaqueta Alpinestars GP Plus R v3',
                    'description': 'Chaqueta de cuero para carreras con protecciones CE y excelente ajuste.',
                    'short_description': 'Chaqueta de cuero deportiva Alpinestars',
                    'brand': 'Alpinestars',
                    'model': 'GP Plus R v3',
                    'price': Decimal('1200000'),
                    'compare_price': Decimal('1400000'),
                    'cost_price': Decimal('850000'),
                    'stock_quantity': 12,
                    'weight': Decimal('2.5'),
                    'dimensions': '65 x 55 x 10 cm',
                    'is_featured': True
                },
                {
                    'name': 'Chaqueta Dainese Racing 4',
                    'description': 'Chaqueta de cuero premium con tecnología D-air compatible.',
                    'short_description': 'Chaqueta cuero Dainese con tecnología D-air',
                    'brand': 'Dainese',
                    'model': 'Racing 4',
                    'price': Decimal('1850000'),
                    'cost_price': Decimal('1300000'),
                    'stock_quantity': 8,
                    'weight': Decimal('2.8'),
                    'dimensions': '65 x 55 x 10 cm'
                }
            ],
            'Guantes de Carreras': [
                {
                    'name': 'Guantes Alpinestars GP Pro R3',
                    'description': 'Guantes de carreras con protección de nudillos y palma reforzada.',
                    'short_description': 'Guantes racing Alpinestars profesionales',
                    'brand': 'Alpinestars',
                    'model': 'GP Pro R3',
                    'price': Decimal('320000'),
                    'compare_price': Decimal('380000'),
                    'cost_price': Decimal('220000'),
                    'stock_quantity': 30,
                    'weight': Decimal('0.3'),
                    'dimensions': '25 x 15 x 5 cm'
                }
            ],
            'Botas de Carretera': [
                {
                    'name': 'Botas Sidi Mag-1',
                    'description': 'Botas de carretera con tecnología de cierre magnético y máxima protección.',
                    'short_description': 'Botas touring Sidi con cierre magnético',
                    'brand': 'Sidi',
                    'model': 'Mag-1',
                    'price': Decimal('750000'),
                    'compare_price': Decimal('850000'),
                    'cost_price': Decimal('520000'),
                    'stock_quantity': 18,
                    'weight': Decimal('1.8'),
                    'dimensions': '35 x 25 x 15 cm',
                    'is_featured': True
                }
            ],
            'Comunicación': [
                {
                    'name': 'Intercomunicador Sena 50S',
                    'description': 'Intercomunicador Bluetooth premium con malla inteligente y alcance extendido.',
                    'short_description': 'Intercomunicador Bluetooth Sena con malla',
                    'brand': 'Sena',
                    'model': '50S',
                    'price': Decimal('680000'),
                    'cost_price': Decimal('480000'),
                    'stock_quantity': 22,
                    'weight': Decimal('0.2'),
                    'dimensions': '10 x 8 x 3 cm',
                    'is_featured': True
                }
            ],
            'Filtros': [
                {
                    'name': 'Filtro de Aire K&N HA-1003',
                    'description': 'Filtro de aire de alto rendimiento para Honda CBR, lavable y reutilizable.',
                    'short_description': 'Filtro aire K&N para Honda CBR series',
                    'brand': 'K&N',
                    'model': 'HA-1003',
                    'price': Decimal('85000'),
                    'compare_price': Decimal('110000'),
                    'cost_price': Decimal('55000'),
                    'stock_quantity': 45,
                    'weight': Decimal('0.4'),
                    'dimensions': '20 x 15 x 5 cm'
                }
            ]
        }

        # Create products
        for category_name, products in products_data.items():
            try:
                category = Category.objects.get(name=category_name)
                
                for product_data in products:
                    product, created = Product.objects.get_or_create(
                        name=product_data['name'],
                        category=category,
                        defaults={
                            **product_data,
                            'status': 'active',
                            'created_by': admin_user,
                            'updated_by': admin_user
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'Created product: {product.name}')
                        
                        # Create product variants for some products
                        if 'Casco' in product.name:
                            sizes = ['S', 'M', 'L', 'XL']
                            for size in sizes:
                                ProductVariant.objects.create(
                                    product=product,
                                    name='Talla',
                                    value=size,
                                    price_adjustment=Decimal('0'),
                                    stock_adjustment=0,
                                    sku_suffix=f'-{size}',
                                    is_active=True
                                )
                        
                        elif 'Chaqueta' in product.name or 'Guantes' in product.name:
                            sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
                            for size in sizes:
                                price_adj = Decimal('20000') if size in ['XXL'] else Decimal('0')
                                ProductVariant.objects.create(
                                    product=product,
                                    name='Talla',
                                    value=size,
                                    price_adjustment=price_adj,
                                    stock_adjustment=0,
                                    sku_suffix=f'-{size}',
                                    is_active=True
                                )
                        
                        elif 'Botas' in product.name:
                            sizes = ['39', '40', '41', '42', '43', '44', '45', '46']
                            for size in sizes:
                                ProductVariant.objects.create(
                                    product=product,
                                    name='Talla',
                                    value=size,
                                    price_adjustment=Decimal('0'),
                                    stock_adjustment=0,
                                    sku_suffix=f'-{size}',
                                    is_active=True
                                )
                                
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Category not found: {category_name}'))

    def create_sample_orders(self):
        self.stdout.write('Creating sample orders...')
        
        customers = User.objects.filter(role='customer')
        products = Product.objects.filter(status='active')
        
        if not customers.exists() or not products.exists():
            self.stdout.write(self.style.WARNING('No customers or products found for orders'))
            return
        
        for customer in customers[:2]:  # Create orders for first 2 customers
            # Create a cart
            cart = Cart.objects.create(user=customer)
            
            # Add random products to cart
            selected_products = random.sample(list(products), min(3, len(products)))
            
            for product in selected_products:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=random.randint(1, 2)
                )
            
            # Create order from cart
            order = Order.objects.create(
                user=customer,
                status='delivered',
                shipping_name=f"{customer.first_name} {customer.last_name}",
                shipping_email=customer.email,
                shipping_phone=customer.phone or '+57 300 000 0000',
                shipping_address=customer.address or 'Dirección de prueba',
                shipping_city='Bogotá',
                shipping_state='Cundinamarca',
                shipping_postal_code='110111',
                shipping_country='Colombia',
                payment_method='credit_card',
                subtotal=Decimal('0'),
                total_amount=Decimal('0')
            )
            
            # Create order items
            total_amount = Decimal('0')
            for cart_item in cart.items.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                total_amount += order_item.get_total_price()
            
            # Update order total
            order.total_amount = total_amount
            order.save()
            
            # Create order status history
            OrderStatusHistory.objects.create(
                order=order,
                status='delivered',
                notes='Orden completada automáticamente',
                created_by_id=1  # Admin user
            )
            
            self.stdout.write(f'Created order for {customer.username}')

    # Removed seeding of sample reviews to keep only real user-generated reviews
    
    def create_categories(self):
        """Create product categories"""
        categories_data = [
            {
                'name': 'Helmets',
                'description': 'High-quality motorcycle helmets for safety and style'
            },
            {
                'name': 'Jackets',
                'description': 'Protective and stylish motorcycle jackets'
            },
            {
                'name': 'Gloves',
                'description': 'Durable motorcycle gloves for better grip and protection'
            },
            {
                'name': 'Boots',
                'description': 'Sturdy motorcycle boots for foot protection'
            },
            {
                'name': 'Accessories',
                'description': 'Various motorcycle accessories and gear'
            },
            {
                'name': 'Parts',
                'description': 'Motorcycle parts and components'
            }
        ]
        
        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
    
    def create_products(self):
        """Create sample products"""
        categories = {cat.name: cat for cat in Category.objects.all()}
        
        products_data = [
            # Helmets
            {
                'name': 'Sport Racing Helmet',
                'description': 'Professional grade racing helmet with advanced aerodynamics and superior protection. Features DOT and ECE certification.',
                'short_description': 'Professional racing helmet with DOT/ECE certification',
                'category': categories['Helmets'],
                'price': Decimal('299.99'),
                'stock': 25,
                'sku': 'HLM-001',
                'brand': 'RaceMax',
                'weight': Decimal('1.5'),
                'is_featured': True
            },
            {
                'name': 'Classic Cruiser Helmet',
                'description': 'Vintage-style open face helmet perfect for cruising. Comfortable fit with premium leather interior.',
                'short_description': 'Vintage-style open face helmet',
                'category': categories['Helmets'],
                'price': Decimal('199.99'),
                'stock': 15,
                'sku': 'HLM-002',
                'brand': 'ClassicRide',
                'weight': Decimal('1.2'),
                'is_featured': True
            },
            # Jackets
            {
                'name': 'Leather Racing Jacket',
                'description': 'Premium leather racing jacket with CE-rated armor inserts. Wind and water resistant with multiple adjustment points.',
                'short_description': 'Premium leather racing jacket with CE armor',
                'category': categories['Jackets'],
                'price': Decimal('449.99'),
                'stock': 20,
                'sku': 'JAC-001',
                'brand': 'SpeedLeather',
                'weight': Decimal('2.5'),
                'is_featured': True
            },
            {
                'name': 'Textile Adventure Jacket',
                'description': 'Versatile textile jacket designed for adventure riding. Waterproof, breathable, and packed with pockets.',
                'short_description': 'Waterproof textile adventure jacket',
                'category': categories['Jackets'],
                'price': Decimal('349.99'),
                'stock': 18,
                'sku': 'JAC-002',
                'brand': 'AdventureGear',
                'weight': Decimal('2.0')
            },
            # Gloves
            {
                'name': 'Sport Riding Gloves',
                'description': 'High-performance riding gloves with carbon fiber knuckle protection and touchscreen compatibility.',
                'short_description': 'Carbon fiber sport gloves with touchscreen tips',
                'category': categories['Gloves'],
                'price': Decimal('89.99'),
                'stock': 30,
                'sku': 'GLV-001',
                'brand': 'ProGrip',
                'weight': Decimal('0.3'),
                'is_featured': True
            },
            {
                'name': 'Winter Heated Gloves',
                'description': 'Battery-heated gloves for cold weather riding. Three heat settings with up to 8 hours of warmth.',
                'short_description': 'Battery-heated gloves for winter riding',
                'category': categories['Gloves'],
                'price': Decimal('159.99'),
                'stock': 12,
                'sku': 'GLV-002',
                'brand': 'WarmRide',
                'weight': Decimal('0.5')
            },
            # Boots
            {
                'name': 'Racing Sport Boots',
                'description': 'Professional racing boots with slider system and shin protection. Excellent for track and sport riding.',
                'short_description': 'Professional racing boots with slider system',
                'category': categories['Boots'],
                'price': Decimal('399.99'),
                'stock': 16,
                'sku': 'BOT-001',
                'brand': 'TrackMaster',
                'weight': Decimal('1.8')
            },
            {
                'name': 'Adventure Touring Boots',
                'description': 'Waterproof adventure boots designed for long-distance touring. Comfortable for walking and riding.',
                'short_description': 'Waterproof adventure touring boots',
                'category': categories['Boots'],
                'price': Decimal('279.99'),
                'stock': 14,
                'sku': 'BOT-002',
                'brand': 'TourGuard',
                'weight': Decimal('1.6'),
                'is_featured': True
            }
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
