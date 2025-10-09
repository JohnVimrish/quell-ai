
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quell AI Frontend Loaded');
    
    // Initialize any interactive components
    initializeComponents();
});

function initializeComponents() {
    // Initialize user menu functionality
    initUserMenu();
    initPhoneParallax();
    console.log('Components initialized');
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`/api${endpoint}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// User menu functionality
function initUserMenu() {
    // Close user menu when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('user-menu');
        const userMenuButton = document.querySelector('.user-menu button');
        
        if (userMenu && userMenuButton && !userMenu.contains(event.target) && !userMenuButton.contains(event.target)) {
            userMenu.classList.remove('show');
        }
    });
}

function toggleUserMenu() {
    const userMenu = document.getElementById('user-menu');
    if (userMenu) {
        userMenu.classList.toggle('show');
    }
}

// Lightweight toast/notification
function showToast(message, type = 'info', duration = 3000) {
    try {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('show'));
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    } catch (e) {
        console.log(message);
    }
}

// Subtle 3D phone tilt
function initPhoneParallax() {
    const phone = document.getElementById('phone-outer');
    if (!phone) return;
    const damp = 30;
    const onMove = (e) => {
        const rect = phone.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        const rotY = (x - 0.5) * 2 * 8; // ±8deg
        const rotX = -(y - 0.5) * 2 * 8;
        phone.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
    };
    const onLeave = () => {
        phone.style.transform = 'rotateX(8deg) rotateY(-8deg)';
    };
    phone.addEventListener('mousemove', onMove);
    phone.addEventListener('mouseleave', onLeave);
}
