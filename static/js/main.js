// Motorcycle World - Frontend JavaScript
class MotorcycleWorldApp {
    constructor() {
        this.apiBase = '/api';
        this.authToken = localStorage.getItem('authToken');
        this.user = JSON.parse(localStorage.getItem('user')) || null;
        this.cart = JSON.parse(localStorage.getItem('cart')) || [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateCartDisplay();
        this.loadFeaturedData();
        this.checkAuthStatus();
    }
    
    setupEventListeners() {
        // Modal controls
        document.getElementById('loginBtn').addEventListener('click', () => this.openModal('loginModal'));
        document.getElementById('registerBtn').addEventListener('click', () => this.openModal('registerModal'));
        document.getElementById('closeLoginModal').addEventListener('click', () => this.closeModal('loginModal'));
        document.getElementById('closeRegisterModal').addEventListener('click', () => this.closeModal('registerModal'));
        
        // Logout links (ensure tokens are cleared before server logout)
        try {
            const logoutLink = document.getElementById('logoutBtn') || document.getElementById('logoutLink');
            if (logoutLink) {
                logoutLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.logout();
                    window.location.href = '/logout/';
                });
            }
            // Fallback: capture any anchor pointing to /logout/
            document.querySelectorAll('a[href="/logout/"]').forEach(a => {
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.logout();
                    window.location.href = '/logout/';
                });
            });
        } catch (err) {}

        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        
        // Cart button
        document.getElementById('cartBtn').addEventListener('click', () => this.openCart());
        
        // Shop now button
        document.getElementById('shopNowBtn').addEventListener('click', () => {
            document.getElementById('products').scrollIntoView({ behavior: 'smooth' });
        });
    }
    
    // Modal management
    openModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
    }
    
    closeModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    }
    
    // Authentication
    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };
        
        try {
            const response = await this.apiCall('/auth/login/', 'POST', data);
            if (response.tokens) {
                this.authToken = response.tokens.access;
                this.user = response.user;
                
                localStorage.setItem('authToken', this.authToken);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                this.showMessage('loginMessage', 'Login successful!', 'success');
                this.closeModal('loginModal');
                this.updateAuthDisplay();
                
                // Redirect based on user role
                if (this.user.is_admin) {
                    window.location.href = '/admin/';
                } else {
                    this.loadUserCart();
                }
            }
        } catch (error) {
            this.showMessage('loginMessage', error.message || 'Login failed', 'error');
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            password: formData.get('password'),
            password_confirm: formData.get('password_confirm')
        };
        
        try {
            const response = await this.apiCall('/auth/register/', 'POST', data);
            if (response.tokens) {
                this.authToken = response.tokens.access;
                this.user = response.user;
                
                localStorage.setItem('authToken', this.authToken);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                this.showMessage('registerMessage', 'Registration successful!', 'success');
                this.closeModal('registerModal');
                this.updateAuthDisplay();
            }
        } catch (error) {
            this.showMessage('registerMessage', error.message || 'Registration failed', 'error');
        }
    }
    
    logout() {
        this.authToken = null;
        this.user = null;
        this.cart = [];
        
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('cart');
        
        this.updateAuthDisplay();
        this.updateCartDisplay();
    }
    
    checkAuthStatus() {
        if (this.authToken && this.user) {
            this.updateAuthDisplay();
            this.loadUserCart();
        }
    }
    
    updateAuthDisplay() {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        
        if (this.user) {
            loginBtn.textContent = `Welcome, ${this.user.username}`;
            loginBtn.onclick = () => this.logout();
            registerBtn.style.display = 'none';
        } else {
            loginBtn.textContent = 'Login';
            loginBtn.onclick = () => this.openModal('loginModal');
            registerBtn.style.display = 'block';
        }
    }
    
    // API calls
    async apiCall(endpoint, method = 'GET', data = null) {
        const url = this.apiBase + endpoint;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (this.authToken) {
            options.headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || result.message || 'API call failed');
        }
        
        return result;
    }
    
    // Data loading
    async loadFeaturedData() {
        try {
            // Load categories
            const categories = await this.apiCall('/products/categories/');
            this.renderCategories(categories.results || categories);
            
            // Load featured products
            const products = await this.apiCall('/products/?is_featured=true');
            this.renderProducts(products.results || products);
        } catch (error) {
            console.error('Error loading featured data:', error);
        }
    }
    
    renderCategories(categories) {
        const grid = document.getElementById('categoriesGrid');
        grid.innerHTML = '';
        
        categories.slice(0, 6).forEach(category => {
            const categoryCard = `
                <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                    <div class="h-48 bg-gradient-to-br from-primary to-gray-600 flex items-center justify-center">
                        <h4 class="text-white text-xl font-bold">${category.name}</h4>
                    </div>
                    <div class="p-4">
                        <p class="text-gray-600">${category.product_count} products</p>
                        <p class="text-sm text-gray-500 mt-2">${category.description || 'Explore our collection'}</p>
                    </div>
                </div>
            `;
            grid.innerHTML += categoryCard;
        });
    }
    
    renderProducts(products) {
        const grid = document.getElementById('productsGrid');
        grid.innerHTML = '';
        
        products.slice(0, 8).forEach(product => {
            const productCard = `
                <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                    <div class="h-48 bg-gray-200 flex items-center justify-center">
                        ${product.primary_image ? 
                            `<img src="${product.primary_image}" alt="${product.name}" class="w-full h-full object-cover">` :
                            `<div class="text-gray-400 text-center">
                                <svg class="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"></path>
                                </svg>
                                <p class="text-sm">No image</p>
                            </div>`
                        }
                    </div>
                    <div class="p-4">
                        <h4 class="font-bold text-lg mb-2">${product.name}</h4>
                        <p class="text-gray-600 text-sm mb-2">${product.short_description || product.category_name}</p>
                        <div class="flex justify-between items-center mb-3">
                            <span class="text-xl font-bold text-secondary">$${product.price}</span>
                            <div class="flex items-center">
                                <span class="text-yellow-400">★</span>
                                <span class="text-sm text-gray-600 ml-1">${product.average_rating.toFixed(1)} (${product.review_count})</span>
                            </div>
                        </div>
                        <button onclick="app.addToCart(${product.id})" 
                                class="w-full bg-secondary text-primary py-2 px-4 rounded-lg hover:bg-yellow-600 transition-colors font-semibold ${!product.is_in_stock ? 'opacity-50 cursor-not-allowed' : ''}"
                                ${!product.is_in_stock ? 'disabled' : ''}>
                            ${product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
                        </button>
                    </div>
                </div>
            `;
            grid.innerHTML += productCard;
        });
    }
    
    // Cart management
    async loadUserCart() {
        if (!this.authToken) return;
        
        try {
            const cart = await this.apiCall('/orders/cart/');
            this.cart = cart.items || [];
            this.updateCartDisplay();
        } catch (error) {
            console.error('Error loading cart:', error);
        }
    }
    
    async addToCart(productId, variantId = null, quantity = 1) {
        if (!this.authToken) {
            this.openModal('loginModal');
            return;
        }
        
        try {
            await this.apiCall('/orders/cart/add/', 'POST', {
                product_id: productId,
                variant_id: variantId,
                quantity: quantity
            });
            
            this.loadUserCart();
            this.showNotification('Product added to cart!', 'success');
        } catch (error) {
            this.showNotification(error.message || 'Failed to add to cart', 'error');
        }
    }
    
    updateCartDisplay() {
        const cartCount = document.getElementById('cartCount');
        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.textContent = totalItems;
    }
    
    openCart() {
        if (!this.authToken) {
            this.openModal('loginModal');
            return;
        }
        // Implement cart modal or redirect to cart page
        alert('Cart functionality will be implemented in cart page');
    }
    
    // Utility functions
    showMessage(elementId, message, type) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.className = `mt-4 text-center ${type === 'success' ? 'text-green-600' : 'text-red-600'}`;
    }
    
    showNotification(message, type) {
        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MotorcycleWorldApp();
});
