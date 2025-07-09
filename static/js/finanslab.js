// FinansLab Interactive Features

// Chart.js configuration for future chart implementations
const chartConfig = {
    type: 'line',
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Backtest Performance'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
};

// Utility functions for animations
const animations = {
    // Fade in element
    fadeIn: (element, duration = 500) => {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    },
    
    // Slide in from bottom
    slideUp: (element, duration = 500) => {
        element.style.transform = 'translateY(50px)';
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const ratio = Math.min(progress / duration, 1);
            
            element.style.transform = `translateY(${50 * (1 - ratio)}px)`;
            element.style.opacity = ratio;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    },
    
    // Scale in
    scaleIn: (element, duration = 300) => {
        element.style.transform = 'scale(0.8)';
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const ratio = Math.min(progress / duration, 1);
            
            element.style.transform = `scale(${0.8 + 0.2 * ratio})`;
            element.style.opacity = ratio;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    }
};

// Form validation utilities
const formValidation = {
    // Validate email format
    isValidEmail: (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Validate ticker symbol
    isValidTicker: (ticker) => {
        const tickerRegex = /^[A-Z]{1,5}$/;
        return tickerRegex.test(ticker);
    },
    
    // Validate date range
    isValidDateRange: (startDate, endDate) => {
        const start = new Date(startDate);
        const end = new Date(endDate);
        return start < end;
    },
    
    // Show field error
    showFieldError: (field, message) => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500 text-sm mt-1 animate-shake';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle mr-1"></i>${message}`;
        
        // Remove existing error
        const existingError = field.parentNode.querySelector('.text-red-500');
        if (existingError) {
            existingError.remove();
        }
        
        field.parentNode.appendChild(errorDiv);
        field.classList.add('border-red-500');
    },
    
    // Clear field error
    clearFieldError: (field) => {
        const errorDiv = field.parentNode.querySelector('.text-red-500');
        if (errorDiv) {
            errorDiv.remove();
        }
        field.classList.remove('border-red-500');
    }
};

// Data visualization utilities
const dataViz = {
    // Format percentage
    formatPercentage: (value) => {
        return `${(value * 100).toFixed(2)}%`;
    },
    
    // Format currency
    formatCurrency: (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    },
    
    // Get color based on performance
    getPerformanceColor: (value, type = 'return') => {
        if (type === 'return') {
            return value > 0 ? 'text-green-600' : 'text-red-600';
        } else if (type === 'sharpe') {
            if (value > 1) return 'text-green-600';
            if (value > 0) return 'text-yellow-600';
            return 'text-red-600';
        }
        return 'text-gray-600';
    },
    
    // Animate counter
    animateCounter: (element, target, duration = 2000) => {
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        };
        requestAnimationFrame(updateCounter);
    }
};

// API utilities
const api = {
    // Make API request with CSRF token
    request: async (url, options = {}) => {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // POST request
    post: (url, data) => {
        return api.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },
    
    // GET request
    get: (url) => {
        return api.request(url, {
            method: 'GET',
        });
    }
};

// UI enhancement utilities
const ui = {
    // Add loading state to button
    setButtonLoading: (button, loading = true) => {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || button.innerHTML;
        }
    },
    
    // Add tooltip to element
    addTooltip: (element, text) => {
        let tooltipTimeout;
        element.addEventListener('mouseenter', (e) => {
            // Remove any existing tooltips
            document.querySelectorAll('.finanslab-tooltip').forEach(t => t.remove());
            const tooltip = document.createElement('div');
            tooltip.className = 'finanslab-tooltip absolute z-50 px-2 py-1 text-sm text-white bg-red-700 rounded shadow-lg'; // RED for debug
            tooltip.textContent = text;
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY - 30 + 'px';
            document.body.appendChild(tooltip);
            element._tooltip = tooltip;
            console.log('Tooltip shown:', text);
            // Auto-remove after 2 seconds
            tooltipTimeout = setTimeout(() => {
                if (tooltip) {
                    tooltip.remove();
                    console.log('Tooltip removed by timeout:', text);
                }
                element._tooltip = null;
            }, 2000);
        });
        
        element.addEventListener('mouseleave', () => {
            if (element._tooltip) {
                element._tooltip.remove();
                element._tooltip = null;
                console.log('Tooltip removed by mouseleave:', text);
            }
            if (tooltipTimeout) clearTimeout(tooltipTimeout);
        });
    },
    
    // Toggle element visibility with animation
    toggleElement: (element, show = true) => {
        if (show) {
            element.style.display = 'block';
            animations.fadeIn(element);
        } else {
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.display = 'none';
            }, 300);
        }
    }
};

// Initialize FinansLab features
document.addEventListener('DOMContentLoaded', function() {
    // Add tooltips to elements with title attribute
    document.querySelectorAll('[title]').forEach(element => {
        ui.addTooltip(element, element.getAttribute('title'));
    });
    
    // Add hover effects to cards
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px) scale(1.02)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                ui.setButtonLoading(submitBtn, true);
            }
        });
    });
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Export utilities for global use
window.FinansLab = {
    animations,
    formValidation,
    dataViz,
    api,
    ui,
    chartConfig
}; 