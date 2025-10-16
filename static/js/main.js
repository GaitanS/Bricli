// Bricli Main JavaScript

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

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Skip if href is just '#' or empty
            if (href === '#' || href.length <= 1) {
                return;
            }
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-hide alerts after 5 seconds (except permanent and action alerts)
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            // Don't auto-hide alerts with buttons/forms (action alerts)
            const hasButtons = alert.querySelector('button, form, a.btn');
            if (!hasButtons) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Enhanced form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();

                // Show first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            form.classList.add('was-validated');
        });

        // Real-time validation for input fields
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });

            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });

    // Phone number validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            // Allow only numbers, spaces, +, -, (, )
            let value = e.target.value.replace(/[^0-9+\-\s\(\)]/g, '');
            e.target.value = value;
        });
    });

    // Budget validation - ensure min <= max
    const budgetMinInput = document.querySelector('#id_budget_min');
    const budgetMaxInput = document.querySelector('#id_budget_max');

    if (budgetMinInput && budgetMaxInput) {
        function validateBudgetRange() {
            const min = parseFloat(budgetMinInput.value) || 0;
            const max = parseFloat(budgetMaxInput.value) || 0;

            if (min > 0 && max > 0 && min > max) {
                budgetMaxInput.setCustomValidity('Bugetul maxim trebuie să fie mai mare decât minimul');
                budgetMinInput.setCustomValidity('Bugetul minim trebuie să fie mai mic decât maximul');
            } else {
                budgetMaxInput.setCustomValidity('');
                budgetMinInput.setCustomValidity('');
            }
        }

        budgetMinInput.addEventListener('input', validateBudgetRange);
        budgetMaxInput.addEventListener('input', validateBudgetRange);
    }

    // Search form enhancements
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="q"]');
        const countySelect = searchForm.querySelector('select[name="county"]');
        
        // Auto-submit on county change
        if (countySelect) {
            countySelect.addEventListener('change', function() {
                if (searchInput.value.trim() || this.value) {
                    searchForm.submit();
                }
            });
        }
    }

    // Image lazy loading
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Rating stars interaction
    const ratingStars = document.querySelectorAll('.rating-input .star');
    ratingStars.forEach((star, index) => {
        star.addEventListener('click', function() {
            const rating = index + 1;
            const ratingInput = this.closest('.rating-input').querySelector('input[type="hidden"]');
            if (ratingInput) {
                ratingInput.value = rating;
            }
            
            // Update visual state
            const allStars = this.closest('.rating-input').querySelectorAll('.star');
            allStars.forEach((s, i) => {
                if (i < rating) {
                    s.classList.remove('far');
                    s.classList.add('fas');
                } else {
                    s.classList.remove('fas');
                    s.classList.add('far');
                }
            });
        });
        
        star.addEventListener('mouseenter', function() {
            const rating = index + 1;
            const allStars = this.closest('.rating-input').querySelectorAll('.star');
            allStars.forEach((s, i) => {
                if (i < rating) {
                    s.style.color = '#8B5CF6';
                } else {
                    s.style.color = '#6b7280';
                }
            });
        });
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const files = this.files;
            const previewContainer = document.querySelector(`#${this.id}-preview`);
            
            if (previewContainer && files.length > 0) {
                previewContainer.innerHTML = '';
                
                Array.from(files).forEach(file => {
                    if (file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const img = document.createElement('img');
                            img.src = e.target.result;
                            img.className = 'img-thumbnail me-2 mb-2';
                            img.style.maxWidth = '100px';
                            img.style.maxHeight = '100px';
                            previewContainer.appendChild(img);
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
        });
    });

    // Dynamic form fields
    const addFieldButtons = document.querySelectorAll('.add-field-btn');
    addFieldButtons.forEach(button => {
        button.addEventListener('click', function() {
            const template = document.querySelector(this.dataset.template);
            const container = document.querySelector(this.dataset.container);
            
            if (template && container) {
                const newField = template.content.cloneNode(true);
                const fieldCount = container.children.length;
                
                // Update field names and IDs
                newField.querySelectorAll('[name]').forEach(field => {
                    const name = field.getAttribute('name');
                    field.setAttribute('name', name.replace('__prefix__', fieldCount));
                    if (field.id) {
                        field.id = field.id.replace('__prefix__', fieldCount);
                    }
                });
                
                container.appendChild(newField);
            }
        });
    });

    // Remove field functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-field-btn')) {
            e.preventDefault();
            const fieldGroup = e.target.closest('.field-group');
            if (fieldGroup) {
                fieldGroup.remove();
            }
        }
    });

    // Price range slider
    const priceSliders = document.querySelectorAll('.price-range-slider');
    priceSliders.forEach(slider => {
        slider.addEventListener('input', function() {
            const output = document.querySelector(this.dataset.output);
            if (output) {
                output.textContent = new Intl.NumberFormat('ro-RO', {
                    style: 'currency',
                    currency: 'RON'
                }).format(this.value);
            }
        });
    });

    // Infinite scroll for lists
    const infiniteScrollContainers = document.querySelectorAll('.infinite-scroll');
    infiniteScrollContainers.forEach(container => {
        const loadMoreUrl = container.dataset.loadMoreUrl;
        let page = 2;
        let loading = false;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !loading) {
                    loading = true;
                    
                    fetch(`${loadMoreUrl}?page=${page}`)
                        .then(response => response.text())
                        .then(html => {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            const newItems = doc.querySelectorAll('.list-item');
                            
                            newItems.forEach(item => {
                                container.appendChild(item);
                            });
                            
                            page++;
                            loading = false;
                            
                            if (newItems.length === 0) {
                                observer.disconnect();
                            }
                        })
                        .catch(error => {
                            console.error('Error loading more items:', error);
                            loading = false;
                        });
                }
            });
        });

        const sentinel = container.querySelector('.load-more-sentinel');
        if (sentinel) {
            observer.observe(sentinel);
        }
    });
});

// Utility functions
function showLoading(element) {
    element.innerHTML = '<span class="loading"></span> Se încarcă...';
    element.disabled = true;
}

function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

function formatPrice(price) {
    return new Intl.NumberFormat('ro-RO', {
        style: 'currency',
        currency: 'RON'
    }).format(price);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('ro-RO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

// AJAX form submission
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    showLoading(submitButton);
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(submitButton, originalText);
        if (data.success) {
            if (successCallback) successCallback(data);
        } else {
            if (errorCallback) errorCallback(data);
        }
    })
    .catch(error => {
        hideLoading(submitButton, originalText);
        console.error('Error:', error);
        if (errorCallback) errorCallback({error: 'A apărut o eroare. Vă rugăm să încercați din nou.'});
    });
}
