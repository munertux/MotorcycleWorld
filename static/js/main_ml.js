// API Base URL
const API_BASE_URL = window.location.origin + '/api';

// Estado de la aplicación
let currentUser = null;
let authToken = localStorage.getItem('authToken') || localStorage.getItem('access_token');
let currentPage = 1;
let currentFilters = {};
let allCategories = [];
let cartItems = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    setupEventListeners();
    await loadCategories();
    await loadFeaturedProducts();
    await loadAllProducts();
    await hydrateAuthFromStorageOrSession();
    // Mostrar confirmación de login si venimos de un redirect
    try {
        const flag = sessionStorage.getItem('login_success');
        if (flag) {
            showToast(flag, 'success');
            sessionStorage.removeItem('login_success');
        }
    } catch (e) {}
    updateCartDisplay();
}

// Reconstruir estado de autenticación desde storage o sesión Django
async function hydrateAuthFromStorageOrSession() {
    // Intentar con usuario cacheado
    try {
        const cached = localStorage.getItem('currentUser');
        if (cached) {
            currentUser = JSON.parse(cached);
            updateAuthUI();
            return;
        }
    } catch (e) {}

    // Intentar obtener perfil con JWT si hay token
    if (authToken) {
        try {
            const res = await fetch(`${API_BASE_URL}/auth/profile/`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${authToken}` },
                credentials: 'same-origin',
            });
            if (res.ok) {
                currentUser = await res.json();
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
                updateAuthUI();
                return;
            }
        } catch (e) {}
    }

    // Intentar con sesión de Django (cookie de sesión)
    try {
        const res = await fetch(`${API_BASE_URL}/auth/profile/`, {
            method: 'GET',
            credentials: 'same-origin',
        });
        if (res.ok) {
            currentUser = await res.json();
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
        }
    } catch (e) {}

    updateAuthUI();
}

// Event Listeners
function setupEventListeners() {
    // Búsqueda
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', debounce(handleSearch, 300));

    // Menús
    document.getElementById('userMenuBtn').addEventListener('click', toggleUserMenu);
    document.getElementById('loginBtn').addEventListener('click', openLoginModal);
    document.getElementById('registerBtn').addEventListener('click', openRegisterModal);
    document.getElementById('logoutBtn').addEventListener('click', logout);

    // Modales
    document.getElementById('closeLoginModal').addEventListener('click', closeLoginModal);
    document.getElementById('closeRegisterModal').addEventListener('click', closeRegisterModal);
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);

    // Cerrar menús al hacer click fuera
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('userDropdown');
        const userBtn = document.getElementById('userMenuBtn');
        
        if (!userBtn.contains(event.target) && !userMenu.contains(event.target)) {
            userMenu.classList.add('hidden');
        }
    });
}

// Funciones de búsqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function handleSearch(event) {
    const query = event.target.value.trim();
    
    if (query.length >= 2) {
        try {
            const response = await fetch(`${API_BASE_URL}/products/search/suggestions/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            showSearchSuggestions(data.suggestions);
        } catch (error) {
            console.error('Error fetching search suggestions:', error);
        }
    } else {
        hideSearchSuggestions();
    }
}

function showSearchSuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    if (!suggestions.products.length && !suggestions.categories.length && !suggestions.brands.length) {
        hideSearchSuggestions();
        return;
    }

    let html = '';
    
    if (suggestions.products.length > 0) {
        html += '<div class="p-2 border-b border-gray-200"><h6 class="text-xs font-semibold text-gray-600 uppercase">Productos</h6></div>';
        suggestions.products.forEach(product => {
            html += `
                <div class="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm">
                    <i class="fas fa-search mr-2 text-gray-400"></i>${product}
                </div>
            `;
        });
    }
    
    if (suggestions.categories.length > 0) {
        html += '<div class="p-2 border-b border-gray-200"><h6 class="text-xs font-semibold text-gray-600 uppercase">Categorías</h6></div>';
        suggestions.categories.forEach(category => {
            html += `
                <div class="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm">
                    <i class="fas fa-folder mr-2 text-gray-400"></i>${category}
                </div>
            `;
        });
    }
    
    if (suggestions.brands.length > 0) {
        html += '<div class="p-2 border-b border-gray-200"><h6 class="text-xs font-semibold text-gray-600 uppercase">Marcas</h6></div>';
        suggestions.brands.forEach(brand => {
            html += `
                <div class="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm">
                    <i class="fas fa-tag mr-2 text-gray-400"></i>${brand}
                </div>
            `;
        });
    }
    
    suggestionsContainer.innerHTML = html;
    suggestionsContainer.classList.remove('hidden');
}

function hideSearchSuggestions() {
    document.getElementById('searchSuggestions').classList.add('hidden');
}

// Funciones de categorías
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/products/categories/tree/`);
        const data = await response.json();
        
        // Handle both array and paginated responses
        allCategories = Array.isArray(data) ? data : (data.results || []);
        
        renderCategoryFilters();
    } catch (error) {
        console.error('Error loading categories:', error);
        allCategories = [];
        renderCategoryFilters();
    }
}

function renderCategoryFilters() {
    const container = document.getElementById('categoryFilters');
    let html = '';
    
    allCategories.forEach(category => {
        html += `
            <div>
                <label class="flex items-center py-1">
                    <input type="checkbox" value="${category.id}" class="mr-2 category-filter">
                    <span class="text-sm">${category.name} (${category.product_count})</span>
                </label>
                ${renderSubcategories(category.children, 1)}
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Event listeners para filtros
    container.addEventListener('change', handleCategoryFilter);
}

function renderSubcategories(children, level) {
    if (!children || children.length === 0) return '';
    
    let html = '';
    const indent = 'ml-' + (level * 4);
    
    children.forEach(child => {
        html += `
            <div class="${indent}">
                <label class="flex items-center py-1">
                    <input type="checkbox" value="${child.id}" class="mr-2 category-filter">
                    <span class="text-sm">${child.name} (${child.product_count})</span>
                </label>
                ${renderSubcategories(child.children, level + 1)}
            </div>
        `;
    });
    
    return html;
}

function handleCategoryFilter(event) {
    if (event.target.classList.contains('category-filter')) {
        const categoryId = event.target.value;
        const isChecked = event.target.checked;
        
        if (isChecked) {
            currentFilters.category = categoryId;
        } else {
            delete currentFilters.category;
        }
        
        loadAllProducts();
    }
}

// Funciones de productos
async function loadFeaturedProducts() {
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}/products/featured/`);
        const products = await response.json();
        renderFeaturedProducts(products);
    } catch (error) {
        console.error('Error loading featured products:', error);
    } finally {
        hideLoading();
    }
}

async function loadAllProducts(page = 1) {
    try {
        showLoading();
        
        let url = `${API_BASE_URL}/products/?page=${page}`;
        
        // Agregar filtros
        const params = new URLSearchParams();
        Object.keys(currentFilters).forEach(key => {
            params.append(key, currentFilters[key]);
        });
        
        if (params.toString()) {
            url += '&' + params.toString();
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        renderProducts(data.results);
        updateProductCount(data.count);
        renderPagination(data);
        
    } catch (error) {
        console.error('Error loading products:', error);
    } finally {
        hideLoading();
    }
}

function renderFeaturedProducts(products) {
    const container = document.getElementById('featuredProducts');
    container.innerHTML = products.map(product => createProductCard(product, true)).join('');
}

function renderProducts(products) {
    const container = document.getElementById('productsGrid');
    container.innerHTML = products.map(product => createProductCard(product)).join('');
}

function createProductCard(product, isFeatured = false) {
    const discountBadge = product.is_on_sale ? 
        `<div class="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded">${product.discount_percentage}% OFF</div>` : '';
    
    const featuredBadge = isFeatured ? 
        '<div class="absolute top-2 right-2 bg-yellow-400 text-yellow-900 text-xs px-2 py-1 rounded">Destacado</div>' : '';
    
    const originalPrice = product.compare_price ? 
        `<span class="text-gray-500 line-through text-sm">$${Number(product.compare_price).toLocaleString()}</span>` : '';
    
    const rating = product.avg_rating > 0 ? 
        `<div class="flex items-center text-sm">
            <div class="flex text-yellow-400">
                ${'★'.repeat(Math.floor(product.avg_rating))}${'☆'.repeat(5 - Math.floor(product.avg_rating))}
            </div>
            <span class="text-gray-500 ml-1">(${product.review_count})</span>
        </div>` : '';
    
    const stockBadge = !product.is_in_stock ? 
        '<div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center"><span class="text-white font-semibold">Agotado</span></div>' : '';

    // Manejar imagen o placeholder
    const imageContent = product.main_image ? 
        `<img src="${product.main_image}" 
             alt="${product.name}" 
             class="w-full h-48 object-cover">` :
        `<div class="w-full h-48 bg-gray-200 flex items-center justify-center">
             <i class="fas fa-image text-4xl text-gray-400"></i>
         </div>`;

    return `
        <div class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300 relative cursor-pointer" 
             onclick="viewProduct('${product.id}')">
            ${discountBadge}
            ${featuredBadge}
            <div class="relative overflow-hidden">
                ${imageContent}
                ${stockBadge}
            </div>
            <div class="p-4">
                <h4 class="font-medium text-gray-900 mb-2 line-clamp-2">${product.name}</h4>
                <p class="text-gray-600 text-sm mb-2 line-clamp-2">${product.short_description || ''}</p>
                
                <div class="flex items-center justify-between mb-2">
                    <div>
                        ${originalPrice}
                        <div class="text-lg font-bold text-gray-900">$${Number(product.price).toLocaleString()}</div>
                    </div>
                </div>
                
                ${rating}
                
                <div class="mt-3 flex items-center justify-between">
                    <span class="text-green-600 text-sm">
                        <i class="fas fa-truck mr-1"></i>Envío gratis
                    </span>
                    <button class="bg-ml-blue text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition-colors" 
                            onclick="event.stopPropagation(); addToCart('${product.id}')">
                        Agregar
                    </button>
                </div>
            </div>
        </div>
    `;
}

function updateProductCount(count) {
    document.getElementById('productCount').textContent = `${count} resultados`;
}

function renderPagination(data) {
    const container = document.getElementById('pagination');
    
    if (!data.next && !data.previous) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<div class="flex items-center space-x-2">';
    
    if (data.previous) {
        html += `
            <button onclick="loadAllProducts(${currentPage - 1})" 
                    class="px-3 py-2 border border-gray-300 rounded hover:bg-gray-100">
                Anterior
            </button>
        `;
    }
    
    html += `<span class="px-3 py-2 text-gray-600">Página ${currentPage}</span>`;
    
    if (data.next) {
        html += `
            <button onclick="loadAllProducts(${currentPage + 1})" 
                    class="px-3 py-2 border border-gray-300 rounded hover:bg-gray-100">
                Siguiente
            </button>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// Funciones de autenticación
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('hidden');
}

function openLoginModal() {
    document.getElementById('loginModal').classList.remove('hidden');
    document.getElementById('userDropdown').classList.add('hidden');
}

function closeLoginModal() {
    document.getElementById('loginModal').classList.add('hidden');
    document.getElementById('loginForm').reset();
    document.getElementById('loginMessage').innerHTML = '';
}

function openRegisterModal() {
    document.getElementById('registerModal').classList.remove('hidden');
    document.getElementById('userDropdown').classList.add('hidden');
}

function closeRegisterModal() {
    document.getElementById('registerModal').classList.add('hidden');
    document.getElementById('registerForm').reset();
    document.getElementById('registerMessage').innerHTML = '';
}

async function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const credentials = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify(credentials)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const access = data.access || (data.tokens && data.tokens.access);
            const refresh = data.refresh || (data.tokens && data.tokens.refresh);
            if (access) {
                authToken = access;
                localStorage.setItem('authToken', access);
                localStorage.setItem('access_token', access);
            }
            if (refresh) {
                localStorage.setItem('refreshToken', refresh);
                localStorage.setItem('refresh_token', refresh);
            }
            currentUser = data.user || currentUser;
            if (currentUser) {
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
            }

            // Mensaje visible de éxito
            showToast('Inicio de sesión exitoso', 'success');
            updateAuthUI();
            closeLoginModal();
        } else {
            showMessage('loginMessage', data.message || 'Error al iniciar sesión', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('loginMessage', 'Error de conexión', 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const userData = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        password_confirm: formData.get('password_confirm')
    };
    
    if (userData.password !== userData.password_confirm) {
        showMessage('registerMessage', 'Las contraseñas no coinciden', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('registerMessage', 'Registro exitoso. Ahora puedes iniciar sesión.', 'success');
            setTimeout(() => {
                closeRegisterModal();
                openLoginModal();
            }, 2000);
        } else {
            showMessage('registerMessage', data.message || 'Error al registrarse', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showMessage('registerMessage', 'Error de conexión', 'error');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('currentUser');
    // Redirigir al endpoint de logout para invalidar la sesión de Django de forma fiable
    window.location.href = '/logout/';
}

// checkAuthStatus ya no se usa; se reemplazó por hydrateAuthFromStorageOrSession

function updateAuthUI() {
    const userDisplayName = document.getElementById('userDisplayName');
    const guestMenu = document.getElementById('guestMenu');
    const userMenu = document.getElementById('userMenu');
    const adminMenuSection = document.getElementById('adminMenuSection');
    
    if (currentUser) {
        userDisplayName.textContent = currentUser.first_name || currentUser.username;
        guestMenu.classList.add('hidden');
        userMenu.classList.remove('hidden');
        
        // Mostrar panel admin si el usuario es administrador o superadmin
        const role = (currentUser.role || '').toLowerCase();
        const isAdminLike = role === 'admin' || role === 'superadmin' || currentUser.is_admin || currentUser.is_staff || currentUser.is_superuser;
        if (isAdminLike) {
            adminMenuSection.classList.remove('hidden');
        } else {
            adminMenuSection.classList.add('hidden');
        }
    } else {
        userDisplayName.textContent = 'Mi cuenta';
        guestMenu.classList.remove('hidden');
        userMenu.classList.add('hidden');
        adminMenuSection.classList.add('hidden');
    }
}

// Funciones de carrito
function addToCart(productId) {
    // Implementar lógica de carrito
    console.log('Adding product to cart:', productId);
    
    // Simulación de agregar al carrito
    cartItems.push({ id: productId, quantity: 1 });
    updateCartDisplay();
    
    // Mostrar mensaje de éxito
    showToast('Producto agregado al carrito', 'success');
}

function updateCartDisplay() {
    const cartCount = document.getElementById('cartCount');
    const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
    
    if (totalItems > 0) {
        cartCount.textContent = totalItems;
        cartCount.classList.remove('hidden');
    } else {
        cartCount.classList.add('hidden');
    }
}

// Funciones de utilidad
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showMessage(containerId, message, type) {
    const container = document.getElementById(containerId);
    const className = type === 'success' ? 'text-green-600' : 'text-red-600';
    container.innerHTML = `<p class="${className}">${message}</p>`;
}

function showToast(message, type = 'info') {
    // Crear elemento de toast
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300 ${
        type === 'success' ? 'bg-green-500 text-white' : 
        type === 'error' ? 'bg-red-500 text-white' : 
        'bg-blue-500 text-white'
    }`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function viewProduct(id) {
    // Navegar a la página de detalle del producto por ID
    window.location.href = `/producto/${id}/`;
}

// Función para aplicar filtros de precio
function applyPriceFilter() {
    const minPrice = document.querySelector('input[placeholder="Mín"]').value;
    const maxPrice = document.querySelector('input[placeholder="Máx"]').value;
    
    if (minPrice) currentFilters.price_min = minPrice;
    if (maxPrice) currentFilters.price_max = maxPrice;
    
    loadAllProducts();
}
