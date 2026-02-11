// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Property image gallery
    const propertyGallery = document.querySelector('.property-gallery');
    if (propertyGallery) {
        const mainImage = propertyGallery.querySelector('.main-image');
        const thumbnails = propertyGallery.querySelectorAll('.thumbnail');

        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                mainImage.src = this.src;
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // Property search form
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const priceRange = searchForm.querySelector('#price-range');
        const priceValue = searchForm.querySelector('#price-value');
        
        if (priceRange) {
            priceRange.addEventListener('input', function() {
                priceValue.textContent = `$${Number(this.value).toLocaleString()}`;
            });
        }

        // Dynamic location search
        const locationInput = searchForm.querySelector('#location');
        if (locationInput) {
            let timeout = null;
            locationInput.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    // Add your location search API call here
                    console.log('Searching location:', this.value);
                }, 500);
            });
        }
    }

    // Favorite property toggle
    const favoriteButtons = document.querySelectorAll('.favorite-button');
    favoriteButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const propertyId = this.dataset.propertyId;
            
            // Check if propertyId is valid
            if (!propertyId || propertyId === 'undefined' || propertyId === 'null') {
                console.error('Invalid property ID for favorite button:', propertyId);
                return;
            }
            
            try {
                const response = await fetch(`/properties/${propertyId}/favorite/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                if (response.ok) {
                    this.classList.toggle('active');
                    const icon = this.querySelector('i');
                    icon.classList.toggle('fas');
                    icon.classList.toggle('far');
                }
            } catch (error) {
                console.error('Error toggling favorite:', error);
            }
        });
    });

    // Property inquiry form
    const inquiryForm = document.querySelector('#inquiry-form');
    if (inquiryForm) {
        inquiryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                if (response.ok) {
                    showAlert('success', 'Your inquiry has been sent successfully!');
                    this.reset();
                } else {
                    showAlert('danger', 'There was an error sending your inquiry. Please try again.');
                }
            } catch (error) {
                console.error('Error submitting inquiry:', error);
                showAlert('danger', 'There was an error sending your inquiry. Please try again.');
            }
        });
    }

    // Message system
    const messageForm = document.querySelector('#message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                if (response.ok) {
                    const messageList = document.querySelector('.message-list');
                    const data = await response.json();
                    messageList.insertAdjacentHTML('beforeend', data.messageHtml);
                    this.reset();
                }
            } catch (error) {
                console.error('Error sending message:', error);
            }
        });
    }

    // Utility functions
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showAlert(type, message) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        const alertContainer = document.querySelector('.alert-container') || document.createElement('div');
        alertContainer.classList.add('alert-container');
        alertContainer.innerHTML = alertHtml;
        document.querySelector('main').insertAdjacentElement('afterbegin', alertContainer);
    }

    // Lazy loading images
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    if ('loading' in HTMLImageElement.prototype) {
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback for browsers that don't support lazy loading
        const lazyImageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => lazyImageObserver.observe(img));
    }

    // Smooth scroll to top
    const scrollToTopBtn = document.querySelector('.scroll-to-top');
    if (scrollToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 100) {
                scrollToTopBtn.classList.add('show');
            } else {
                scrollToTopBtn.classList.remove('show');
            }
        });

        scrollToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}); 