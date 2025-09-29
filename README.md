# Motorcycle World - Plataforma E-commerce

Una plataforma de e-commerce integral basada en Django especializada en accesorios y equipos para motocicletas, con arquitectura de API REST, autenticación JWT, resúmenes de reseñas con IA y frontend responsivo.

## 🚀 Características

### Funcionalidad Principal
- **Gestión de Usuarios**: Modelo de usuario personalizado con permisos basados en roles (Admin/Cliente)
- **Catálogo de Productos**: Gestión completa de productos con categorías, variantes e imágenes
- **Carrito de Compras**: Funcionalidad completa de carrito con persistencia de sesión
- **Gestión de Pedidos**: Flujo completo de procesamiento de pedidos con seguimiento de estado
- **Sistema de Reseñas**: Reseñas de clientes con resúmenes con IA usando OpenAI GPT
- **Búsqueda y Filtrado**: Capacidades avanzadas de búsqueda y filtrado de productos

### Características Técnicas
- **API REST**: API REST completa usando Django REST Framework
- **Autenticación JWT**: Autenticación segura basada en tokens
- **Base de Datos**: Esquema normalizado diseñado para MariaDB/MySQL
- **Integración de IA**: API de OpenAI para resúmenes inteligentes de reseñas
- **Diseño Responsivo**: Diseño mobile-first usando Tailwind CSS
- **Panel de Administración**: Interfaz de administración integral para gestión

## 🛠 Stack Tecnológico

### Backend
- **Django 5.0.2**: Framework web
- **Django REST Framework**: Desarrollo de API
- **Simple JWT**: Autenticación JWT
- **MariaDB/MySQL**: Base de datos principal
- **API OpenAI**: Características con IA
- **Celery**: Procesamiento de tareas asíncronas
- **Redis**: Cache y broker de mensajes

### Frontend
- **Tailwind CSS**: Framework de estilos
- **JavaScript Vanilla**: Interacciones del frontend
- **Django Templates**: Renderizado del lado del servidor

### Despliegue
- **Gunicorn**: Servidor HTTP WSGI
- **WhiteNoise**: Servir archivos estáticos
- **Listo para AWS**: Configurado para despliegue EC2 + RDS

## 📋 Prerrequisitos

- Python 3.12+
- MariaDB/MySQL 8.0+
- Redis (para Celery)
- Node.js (para desarrollo con Tailwind CSS)

## 🔧 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/munertux/MotorcycleWorld.git
cd MotorcycleWorld
```

### 2. Crear Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configuración de la Base de Datos
1. Crear una base de datos MariaDB/MySQL llamada `Test_Final`
2. Actualizar el archivo `.env` con las credenciales de tu base de datos:

```env
# Configuración de Base de Datos
USE_MYSQL=True
DB_NAME=Test_Final
DB_USER=root
DB_PASSWORD=TadsDb
DB_HOST=127.0.0.1
DB_PORT=3310

# Configuración OpenAI (opcional)
OPENAI_API_KEY=tu-api-key-de-openai-aqui

# Configuración Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7. Poblar Datos de Ejemplo
```bash
python manage.py populate_db
```

### 8. Ejecutar Servidor de Desarrollo
```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000`

## 🗂 Estructura del Proyecto

```
MotorcycleWorld/
├── motorcycle_world/          # Configuración principal del proyecto
├── users/                     # App de gestión de usuarios
├── products/                  # App de catálogo de productos
├── orders/                    # App de gestión de pedidos
├── reviews/                   # App del sistema de reseñas
├── services/                  # Capa de lógica de negocio
├── templates/                 # Plantillas HTML
├── static/                    # Archivos estáticos (CSS, JS)
├── media/                     # Archivos subidos por usuarios
├── requirements.txt           # Dependencias de Python
├── .env.example              # Plantilla de variables de entorno
└── README.md                 # Este archivo
```

## 🔌 Endpoints de la API

### Autenticación
- `POST /api/auth/register/` - Registro de usuario
- `POST /api/auth/login/` - Inicio de sesión de usuario
- `POST /api/auth/token/refresh/` - Renovar token JWT
- `GET /api/auth/profile/` - Obtener perfil de usuario
- `PUT /api/auth/profile/` - Actualizar perfil de usuario

### Productos
- `GET /api/products/` - Listar productos
- `GET /api/products/{id}/` - Detalle de producto
- `GET /api/products/categories/` - Listar categorías
- `POST /api/products/` - Crear producto (solo admin)
- `PUT /api/products/{id}/` - Actualizar producto (solo admin)

### Pedidos
- `GET /api/orders/cart/` - Obtener carrito del usuario
- `POST /api/orders/cart/add/` - Agregar artículo al carrito
- `POST /api/orders/checkout/` - Crear pedido desde el carrito
- `GET /api/orders/` - Listar pedidos del usuario
- `GET /api/orders/{id}/` - Detalle de pedido

### Reseñas
- `GET /api/reviews/` - Listar reseñas
- `POST /api/reviews/` - Crear reseña
- `GET /api/reviews/summary/{product_id}/` - Obtener resumen de reseñas con IA

## 👤 Roles de Usuario

### Cliente
- Navegar y buscar productos
- Agregar artículos al carrito y realizar pedidos
- Escribir reseñas de productos
- Gestionar perfil y ver historial de pedidos

### Administrador
- Gestión completa de productos (CRUD)
- Gestión de pedidos y actualizaciones de estado
- Gestión de usuarios
- Moderación de reseñas
- Acceso al panel de administración

## 🤖 Características de IA

### Resúmenes de Reseñas
El sistema utiliza los modelos GPT de OpenAI para generar resúmenes inteligentes de las reseñas de clientes:

- **Generación Automática**: Los resúmenes se crean cuando se agregan nuevas reseñas
- **Análisis de Sentimiento**: La IA analiza el sentimiento general (positivo/negativo/neutral)
- **Perspectivas Clave**: Destaca temas comunes en los comentarios de los clientes
- **Modo de Respaldo**: Proporciona resúmenes básicos cuando la IA no está disponible

Para habilitar las características de IA:
1. Obtén una clave API de OpenAI desde https://platform.openai.com/
2. Agrégala a tu archivo `.env`: `OPENAI_API_KEY=tu-api-key`

## 🚀 Despliegue

### Desarrollo
```bash
python manage.py runserver
```

### Producción (AWS EC2)
1. **Instancia EC2**: Desplegar app Django con Gunicorn + Nginx
2. **RDS**: Usar Amazon RDS para la base de datos MariaDB
3. **S3**: Almacenar archivos estáticos y subidas de media
4. **Variables de Entorno**: Usar AWS Systems Manager o user data de EC2

Ejemplo de comando para producción:
```bash
gunicorn --bind 0.0.0.0:8000 motorcycle_world.wsgi:application
```

## 🧪 Pruebas

### Ejecutar Pruebas
```bash
python manage.py test
```

### Pruebas de API
Usa la colección de Postman proporcionada o prueba endpoints con curl:

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","password_confirm":"testpass123"}'

# Iniciar sesión
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

## 📝 Usuarios por Defecto

Después de ejecutar `populate_db`, los siguientes usuarios están disponibles:

- **Admin**: `admin` / `admin123`
- **Cliente**: `john_rider` / `customer123`
- **Cliente**: `sarah_biker` / `customer123`

## 🔒 Características de Seguridad

- Autenticación basada en JWT
- Hash de contraseñas con el sistema integrado de Django
- Configuración CORS para solicitudes de origen cruzado
- Protección CSRF para formularios
- Prevención de inyección SQL a través del ORM
- Control de acceso basado en roles

## 📈 Optimización de Rendimiento

- Optimización de consultas de base de datos con select_related/prefetch_related
- Compresión de archivos estáticos con WhiteNoise
- Optimización de imágenes para fotos de productos
- Paginación para conjuntos de datos grandes
- Cache de Redis para datos de sesión
