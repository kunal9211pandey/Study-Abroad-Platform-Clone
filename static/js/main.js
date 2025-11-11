// ApplyBoard Main JavaScript File

// Global variables
let isScrolled = false;
let countAnimated = false;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeCounters();
    initializeFormValidation();
    initializeScrollAnimations();
    initializeSearchFunctionality();
    initializeCarousels();
    initializeLazyLoading();
});

// Navigation Functions
function initializeNavigation() {
    const navbar = document.querySelector('.navbar');
    
    // Handle scroll effects
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 50 && !isScrolled) {
            navbar.classList.add('scrolled');
            isScrolled = true;
        } else if (scrollTop <= 50 && isScrolled) {
            navbar.classList.remove('scrolled');
            isScrolled = false;
        }
    });

    // Mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            const navbarCollapse = document.querySelector('.navbar-collapse');
            navbarCollapse.classList.toggle('show');
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
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
}

// Counter Animation
function initializeCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    const animateCounter = (counter) => {
        const target = parseInt(counter.getAttribute('data-target'));
        const increment = target / 200;
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = formatNumber(target);
                clearInterval(timer);
            } else {
                counter.textContent = formatNumber(Math.ceil(current));
            }
        }, 10);
    };

    const formatNumber = (num) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M+';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(0) + 'K+';
        }
        return num.toString() + '+';
    };

    // Intersection Observer for counter animation
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !countAnimated) {
                counters.forEach(counter => animateCounter(counter));
                countAnimated = true;
            }
        });
    }, observerOptions);

    // Observe the statistics section
    const statsSection = document.querySelector('.stat-card');
    if (statsSection) {
        observer.observe(statsSection);
    }
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                showFormErrors(form);
            } else {
                showLoadingState(form);
            }
            form.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(input);
            });

            input.addEventListener('input', function() {
                if (input.classList.contains('is-invalid')) {
                    validateField(input);
                }
            });
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    field.classList.toggle('is-valid', isValid);
    field.classList.toggle('is-invalid', !isValid);
    
    // Show/hide custom error messages
    const errorMsg = field.parentNode.querySelector('.invalid-feedback');
    if (errorMsg) {
        errorMsg.style.display = isValid ? 'none' : 'block';
    }
}

function showFormErrors(form) {
    const firstInvalidField = form.querySelector('.is-invalid, :invalid');
    if (firstInvalidField) {
        firstInvalidField.focus();
        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function showLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        // Reset after 3 seconds (in case form doesn't redirect)
        setTimeout(() => {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }, 3000);
    }
}

// Scroll Animations
function initializeScrollAnimations() {
    const animateElements = document.querySelectorAll('[class*="animate-"]');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    animateElements.forEach(element => {
        element.style.animationPlayState = 'paused';
        observer.observe(element);
    });
}

// Search Functionality
function initializeSearchFunctionality() {
    const searchForm = document.querySelector('.search-form');
    const countrySelect = document.querySelector('.country-select');
    
    if (countrySelect) {
        // Add flag icons to country options
        countrySelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const flag = selectedOption.getAttribute('data-flag');
            if (flag) {
                this.style.backgroundImage = `url("data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="30">' + flag + '</text></svg>')}")`;
                this.style.backgroundSize = '20px 20px';
                this.style.backgroundRepeat = 'no-repeat';
                this.style.backgroundPosition = '10px center';
                this.style.paddingLeft = '40px';
            }
        });
    }

    // Search suggestions
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                showSearchSuggestions(this.value);
            }, 300);
        });
    }
}

function showSearchSuggestions(query) {
    if (query.length < 2) return;
    
    // Mock search suggestions
    const suggestions = [
        'University of Toronto',
        'Harvard University',
        'Oxford University',
        'MIT',
        'Stanford University',
        'Cambridge University'
    ].filter(item => item.toLowerCase().includes(query.toLowerCase()));

    // Create suggestions dropdown (simplified)
    console.log('Search suggestions:', suggestions);
}

// Carousel Initialization
function initializeCarousels() {
    const carousels = document.querySelectorAll('.carousel');
    
    carousels.forEach(carousel => {
        // Auto-play carousel
        const carouselInstance = new bootstrap.Carousel(carousel, {
            interval: 5000,
            ride: 'carousel'
        });

        // Pause on hover
        carousel.addEventListener('mouseenter', () => {
            carouselInstance.pause();
        });

        carousel.addEventListener('mouseleave', () => {
            carouselInstance.cycle();
        });
    });
}

// Lazy Loading
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Utility Functions
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

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Cookie Consent (GDPR Compliance)
function initializeCookieConsent() {
    const cookieConsent = localStorage.getItem('cookieConsent');
    
    if (!cookieConsent) {
        showCookieBanner();
    }
}

function showCookieBanner() {
    const banner = document.createElement('div');
    banner.className = 'cookie-banner position-fixed bottom-0 start-0 end-0 bg-dark text-white p-3 d-flex justify-content-between align-items-center';
    banner.style.zIndex = '9999';
    banner.innerHTML = `
        <span>We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.</span>
        <button class="btn btn-sm btn-warning ms-3" onclick="acceptCookies()">Accept</button>
    `;
    document.body.appendChild(banner);
}

function acceptCookies() {
    localStorage.setItem('cookieConsent', 'accepted');
    const banner = document.querySelector('.cookie-banner');
    if (banner) {
        banner.remove();
    }
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    // You could send this to an error tracking service
});

// Performance Monitoring
function measurePageLoadTime() {
    window.addEventListener('load', function() {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log('Page load time:', loadTime + 'ms');
        
        // You could send this data to an analytics service
        if (window.gtag) {
            gtag('event', 'timing_complete', {
                name: 'load',
                value: loadTime
            });
        }
    });
}

// Initialize performance monitoring
measurePageLoadTime();

// Initialize cookie consent
initializeCookieConsent();

// Export functions for global use
window.ApplyBoard = {
    showSearchSuggestions,
    acceptCookies,
    validateField,
    debounce,
    throttle
};
