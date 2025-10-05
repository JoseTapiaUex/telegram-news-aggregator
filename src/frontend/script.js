/**
 * Script principal del frontend del News Aggregator
 * Ruta: src/frontend/script.js
 */

// Configuración
const CONFIG = {
    apiBaseUrl: 'http://localhost:5000/api',
    refreshInterval: 30000, // 30 segundos
    animationDelay: 50 // ms entre animaciones de cards
};

// Estado de la aplicación
const AppState = {
    posts: [],
    filteredPosts: [],
    providers: new Set(),
    types: new Set(),
    stats: null,
    filters: {
        search: '',
        provider: '',
        type: ''
    }
};

// Elementos del DOM
const Elements = {
    postsContainer: null,
    loadingIndicator: null,
    emptyState: null,
    searchInput: null,
    providerFilter: null,
    typeFilter: null,
    clearFiltersBtn: null,
    totalPosts: null,
    totalProviders: null,
    lastUpdate: null
};

/**
 * Inicialización de la aplicación
 */
function init() {
    console.log('[INFO] Inicializando aplicación...');
    
    // Cachear elementos del DOM
    cacheElements();
    
    // Configurar event listeners
    setupEventListeners();
    
    // Cargar datos iniciales
    loadPosts();
    
    // Configurar recarga automática
    setupAutoRefresh();
    
    console.log('[INFO] Aplicación iniciada correctamente');
}

/**
 * Cachea referencias a elementos del DOM
 */
function cacheElements() {
    Elements.postsContainer = document.getElementById('postsContainer');
    Elements.loadingIndicator = document.getElementById('loadingIndicator');
    Elements.emptyState = document.getElementById('emptyState');
    Elements.searchInput = document.getElementById('searchInput');
    Elements.providerFilter = document.getElementById('providerFilter');
    Elements.typeFilter = document.getElementById('typeFilter');
    Elements.clearFiltersBtn = document.getElementById('clearFilters');
    Elements.totalPosts = document.getElementById('totalPosts');
    Elements.totalProviders = document.getElementById('totalProviders');
    Elements.lastUpdate = document.getElementById('lastUpdate');
}

/**
 * Configura los event listeners
 */
function setupEventListeners() {
    // Búsqueda con debounce
    Elements.searchInput.addEventListener('input', debounce((e) => {
        AppState.filters.search = e.target.value.toLowerCase();
        applyFilters();
    }, 300));
    
    // Filtro de proveedor
    Elements.providerFilter.addEventListener('change', (e) => {
        AppState.filters.provider = e.target.value;
        applyFilters();
    });
    
    // Filtro de tipo
    Elements.typeFilter.addEventListener('change', (e) => {
        AppState.filters.type = e.target.value;
        applyFilters();
    });
    
    // Limpiar filtros
    Elements.clearFiltersBtn.addEventListener('click', clearFilters);
}

/**
 * Carga los posts desde el API
 */
async function loadPosts() {
    try {
        showLoading(true);
        
        // Cargar posts
        const postsResponse = await fetch(`${CONFIG.apiBaseUrl}/posts`);
        
        if (!postsResponse.ok) {
            throw new Error(`Error HTTP: ${postsResponse.status}`);
        }
        
        const postsData = await postsResponse.json();
        
        if (postsData.success) {
            AppState.posts = postsData.posts;
            AppState.filteredPosts = [...AppState.posts];
            
            // Extraer proveedores y tipos únicos
            extractFilters();
            
            // Actualizar UI
            updateFilterOptions();
            renderPosts();
            
            console.log(`[INFO] ${AppState.posts.length} posts cargados`);
        }
        
        // Cargar estadísticas
        await loadStats();
        
    } catch (error) {
        console.error('[ERROR] Error cargando posts:', error);
        showError('No se pudieron cargar los posts. Verifica que el servidor esté corriendo.');
    } finally {
        showLoading(false);
    }
}

/**
 * Carga las estadísticas desde el API
 */
async function loadStats() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/stats`);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            AppState.stats = data.stats;
            updateStats();
        }
    } catch (error) {
        console.error('[ERROR] Error cargando estadísticas:', error);
    }
}

/**
 * Extrae proveedores y tipos únicos de los posts
 */
function extractFilters() {
    AppState.providers.clear();
    AppState.types.clear();
    
    AppState.posts.forEach(post => {
        if (post.provider) {
            AppState.providers.add(post.provider);
        }
        if (post.type) {
            AppState.types.add(post.type);
        }
    });
}

/**
 * Actualiza las opciones de los filtros
 */
function updateFilterOptions() {
    // Actualizar filtro de proveedores
    Elements.providerFilter.innerHTML = '<option value="">Todos los proveedores</option>';
    Array.from(AppState.providers).sort().forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider;
        Elements.providerFilter.appendChild(option);
    });
    
    // Actualizar filtro de tipos
    Elements.typeFilter.innerHTML = '<option value="">Todos los tipos</option>';
    Array.from(AppState.types).sort().forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        Elements.typeFilter.appendChild(option);
    });
}

/**
 * Aplica los filtros activos
 */
function applyFilters() {
    AppState.filteredPosts = AppState.posts.filter(post => {
        // Filtro de búsqueda
        if (AppState.filters.search) {
            const searchLower = AppState.filters.search;
            const matchesSearch = 
                post.title.toLowerCase().includes(searchLower) ||
                post.summary.toLowerCase().includes(searchLower) ||
                (post.provider && post.provider.toLowerCase().includes(searchLower));
            
            if (!matchesSearch) return false;
        }
        
        // Filtro de proveedor
        if (AppState.filters.provider && post.provider !== AppState.filters.provider) {
            return false;
        }
        
        // Filtro de tipo
        if (AppState.filters.type && post.type !== AppState.filters.type) {
            return false;
        }
        
        return true;
    });
    
    renderPosts();
}

/**
 * Limpia todos los filtros
 */
function clearFilters() {
    AppState.filters = {
        search: '',
        provider: '',
        type: ''
    };
    
    Elements.searchInput.value = '';
    Elements.providerFilter.value = '';
    Elements.typeFilter.value = '';
    
    AppState.filteredPosts = [...AppState.posts];
    renderPosts();
}

/**
 * Renderiza los posts en el contenedor
 */
function renderPosts() {
    Elements.postsContainer.innerHTML = '';
    
    if (AppState.filteredPosts.length === 0) {
        showEmptyState(true);
        return;
    }
    
    showEmptyState(false);
    
    AppState.filteredPosts.forEach((post, index) => {
        const postCard = createPostCard(post, index);
        Elements.postsContainer.appendChild(postCard);
    });
}

/**
 * Crea un card de post
 */
function createPostCard(post, index) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.style.animationDelay = `${index * CONFIG.animationDelay}ms`;
    
    // Imagen
    const imageContainer = document.createElement('div');
    imageContainer.className = 'post-image-container';
    
    if (post.image_url) {
        const img = document.createElement('img');
        img.className = 'post-image';
        img.src = post.image_url;
        img.alt = post.title;
        img.onerror = () => {
            img.style.display = 'none';
            imageContainer.appendChild(createImagePlaceholder(post.type));
        };
        imageContainer.appendChild(img);
    } else {
        imageContainer.appendChild(createImagePlaceholder(post.type));
    }
    
    // Contenido
    const content = document.createElement('div');
    content.className = 'post-content';
    
    // Header con metadata
    const header = document.createElement('div');
    header.className = 'post-header';
    
    const meta = document.createElement('div');
    meta.className = 'post-meta';
    
    const provider = document.createElement('span');
    provider.className = 'post-provider';
    provider.textContent = post.provider || 'Desconocido';
    
    const date = document.createElement('span');
    date.className = 'post-date';
    date.textContent = formatDate(post.release_date);
    
    meta.appendChild(provider);
    meta.appendChild(date);
    
    const type = document.createElement('span');
    type.className = 'post-type';
    type.textContent = post.type || 'Otro';
    
    header.appendChild(meta);
    header.appendChild(type);
    
    // Título
    const title = document.createElement('h3');
    title.className = 'post-title';
    title.textContent = post.title;
    
    // Resumen
    const summary = document.createElement('p');
    summary.className = 'post-summary';
    summary.textContent = post.summary;
    
    // Footer con enlace
    const footer = document.createElement('div');
    footer.className = 'post-footer';
    
    const link = document.createElement('a');
    link.className = 'post-link';
    link.href = post.source_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Leer más';
    
    footer.appendChild(link);
    
    // Ensamblar card
    content.appendChild(header);
    content.appendChild(title);
    content.appendChild(summary);
    content.appendChild(footer);
    
    card.appendChild(imageContainer);
    card.appendChild(content);
    
    // Click en toda la card abre el enlace
    card.addEventListener('click', (e) => {
        if (e.target.tagName !== 'A') {
            window.open(post.source_url, '_blank', 'noopener,noreferrer');
        }
    });
    
    return card;
}

/**
 * Crea un placeholder para imágenes
 */
function createImagePlaceholder(type) {
    const placeholder = document.createElement('div');
    placeholder.className = 'post-image-placeholder';
    
    const emojis = {
        'Artículo de Blog': '📝',
        'Noticia': '📰',
        'Video': '🎥',
        'Investigación': '🔬',
        'Tutorial': '📚',
        'Documentación': '📖',
        'Otro': '📄'
    };
    
    placeholder.textContent = emojis[type] || '📄';
    
    return placeholder;
}

/**
 * Actualiza las estadísticas en el UI
 */
function updateStats() {
    if (!AppState.stats) return;
    
    // Total de posts
    Elements.totalPosts.textContent = AppState.stats.total_posts || 0;
    
    // Total de proveedores
    Elements.totalProviders.textContent = AppState.stats.by_provider?.length || 0;
    
    // Última actualización
    Elements.lastUpdate.textContent = formatTime(new Date());
}

/**
 * Muestra/oculta el indicador de carga
 */
function showLoading(show) {
    if (show) {
        Elements.loadingIndicator.classList.add('active');
        Elements.postsContainer.style.display = 'none';
    } else {
        Elements.loadingIndicator.classList.remove('active');
        Elements.postsContainer.style.display = 'grid';
    }
}

/**
 * Muestra/oculta el estado vacío
 */
function showEmptyState(show) {
    Elements.emptyState.style.display = show ? 'block' : 'none';
    Elements.postsContainer.style.display = show ? 'none' : 'grid';
}

/**
 * Muestra un mensaje de error
 */
function showError(message) {
    Elements.emptyState.innerHTML = `
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <h2>Error de Conexión</h2>
        <p>${message}</p>
    `;
    showEmptyState(true);
}

/**
 * Configura la recarga automática
 */
function setupAutoRefresh() {
    setInterval(() => {
        console.log('[INFO] Recargando datos automáticamente...');
        loadPosts();
    }, CONFIG.refreshInterval);
}

/**
 * Formatea una fecha
 */
function formatDate(dateString) {
    if (!dateString) return 'Fecha desconocida';
    
    try {
        const date = new Date(dateString);
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('es-ES', options);
    } catch (error) {
        return dateString;
    }
}

/**
 * Formatea una hora
 */
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * Función debounce para optimizar búsquedas
 */
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

/**
 * Verifica el estado del API
 */
async function checkApiHealth() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/health`);
        const data = await response.json();
        
        if (data.success) {
            console.log('[INFO] API funcionando correctamente');
            return true;
        }
    } catch (error) {
        console.error('[ERROR] API no disponible:', error);
        return false;
    }
}

// Iniciar la aplicación cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Verificar estado del API al iniciar
checkApiHealth();