
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quell AI Frontend Loaded');
    
    // Initialize any interactive components
    initializeComponents();
});

function initializeComponents() {
    // Add any JavaScript functionality here
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

// AI Mode toggle functionality
async function toggleAIMode() {
    try {
        const result = await apiCall('/ai-mode/toggle', {
            method: 'POST'
        });
        
        console.log('AI Mode toggled:', result);
        updateAIModeUI(result.ai_mode_active);
        
    } catch (error) {
        console.error('Failed to toggle AI mode:', error);
    }
}

function updateAIModeUI(isActive) {
    const toggleButton = document.getElementById('ai-mode-toggle');
    if (toggleButton) {
        toggleButton.textContent = isActive ? 'Disable AI Mode' : 'Enable AI Mode';
        toggleButton.className = isActive ? 'btn btn-danger' : 'btn btn-primary';
    }
}
