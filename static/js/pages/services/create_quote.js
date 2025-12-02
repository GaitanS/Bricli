// Toggle description expand/collapse
function toggleDescription() {
    const shortDiv = document.getElementById('order-description-short');
    const fullDiv = document.getElementById('order-description-full');

    if (fullDiv.style.display === 'none') {
        shortDiv.style.display = 'none';
        fullDiv.style.display = 'block';
    } else {
        shortDiv.style.display = 'block';
        fullDiv.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // ========================================
    // Initialize Flatpickr Date Picker
    // ========================================
    const dateInput = document.getElementById('id_proposed_start_date');
    if (dateInput) {
        flatpickr(dateInput, {
            locale: 'ro',
            dateFormat: 'Y-m-d',
            minDate: 'today',
            maxDate: new Date().fp_incr(365), // 1 year from today
            altInput: true,
            altFormat: 'd F Y', // Display format: "15 ianuarie 2025"
            allowInput: true,
            clickOpens: true,
            disableMobile: false, // Use Flatpickr on mobile too
            monthSelectorType: 'dropdown',
            yearSelectorType: 'dropdown',
            prevArrow: '<svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24"><path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z"/></svg>',
            nextArrow: '<svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24"><path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/></svg>',
            onReady: function (selectedDates, dateStr, instance) {
                // Add calendar icon click handler
                const input = instance.altInput || instance.input;
                input.style.cursor = 'pointer';
            }
        });
    }

    // ========================================
    // Character counter for description
    // ========================================
    const descriptionTextarea = document.getElementById('id_description');
    const charCount = document.getElementById('char-count');

    if (descriptionTextarea && charCount) {
        // Initial count
        charCount.textContent = descriptionTextarea.value.length;

        // Update on input
        descriptionTextarea.addEventListener('input', function () {
            const count = this.value.length;
            charCount.textContent = count;

            // Change color based on length
            if (count < 100) {
                charCount.style.color = '#ef4444'; // Red
            } else if (count < 200) {
                charCount.style.color = '#f59e0b'; // Orange
            } else {
                charCount.style.color = '#10b981'; // Green
            }
        });

        // Auto-resize textarea
        descriptionTextarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // Format price input
    const priceInput = document.getElementById('id_price');
    if (priceInput) {
        priceInput.addEventListener('input', function (e) {
            // Remove non-numeric characters except decimal point
            let value = e.target.value.replace(/[^\d.]/g, '');

            // Ensure only one decimal point
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }

            // Limit decimal places to 2
            if (parts[1] && parts[1].length > 2) {
                value = parts[0] + '.' + parts[1].substring(0, 2);
            }

            e.target.value = value;
        });

        // Highlight on focus
        priceInput.addEventListener('focus', function () {
            this.parentElement.style.transform = 'scale(1.02)';
            this.parentElement.style.transition = 'transform 0.2s ease';
        });

        priceInput.addEventListener('blur', function () {
            this.parentElement.style.transform = 'scale(1)';
        });
    }

    // Form validation feedback
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('.btn-submit-quote');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Se trimite...';
                submitBtn.disabled = true;
            }
        });
    }

    // Smooth scroll to form errors
    const firstError = document.querySelector('.text-danger');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
