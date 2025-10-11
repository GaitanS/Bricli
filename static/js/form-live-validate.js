/**
 * Live Form Validation
 * Provides real-time client-side validation with Bootstrap 5 styling
 *
 * Usage: Add class "needs-live-validate" to any form
 * Ensure each field has a sibling <div class="invalid-feedback"></div>
 */
(function() {
    'use strict';

    /**
     * Mark field as invalid with error message
     */
    function invalidate(element, message) {
        element.classList.add('is-invalid');
        element.classList.remove('is-valid');

        let feedback = element.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            element.parentElement.appendChild(feedback);
        }
        feedback.textContent = message;
        feedback.style.display = 'block';
    }

    /**
     * Clear invalid state from field
     */
    function clearInvalid(element) {
        element.classList.remove('is-invalid');
        element.classList.add('is-valid');

        const feedback = element.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = '';
            feedback.style.display = 'none';
        }
    }

    /**
     * Validate single field
     */
    function validateField(field) {
        if (!field.checkValidity()) {
            const message = field.validationMessage || 'Completează corect acest câmp.';
            invalidate(field, message);
            return false;
        } else {
            clearInvalid(field);
            return true;
        }
    }

    /**
     * Bind validation events to form
     */
    function bindFormValidation(form) {
        const fields = form.querySelectorAll('input, select, textarea');

        // Validate on input (while typing)
        fields.forEach(field => {
            field.addEventListener('input', () => {
                if (field.classList.contains('is-invalid') || field.classList.contains('is-valid')) {
                    validateField(field);
                }
            });

            // Validate on blur (when leaving field)
            field.addEventListener('blur', () => {
                validateField(field);
            });
        });

        // Validate on submit
        form.addEventListener('submit', (e) => {
            let firstInvalidField = null;
            let isFormValid = true;

            fields.forEach(field => {
                if (!validateField(field)) {
                    isFormValid = false;
                    if (!firstInvalidField) {
                        firstInvalidField = field;
                    }
                }
            });

            if (!isFormValid) {
                e.preventDefault();

                // Scroll to first error
                if (firstInvalidField) {
                    firstInvalidField.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });

                    // Focus after scroll completes
                    setTimeout(() => {
                        firstInvalidField.focus({ preventScroll: true });
                    }, 300);
                }
            }
        });
    }

    /**
     * Initialize on DOM ready
     */
    document.addEventListener('DOMContentLoaded', () => {
        const forms = document.querySelectorAll('form.needs-live-validate');
        forms.forEach(bindFormValidation);
    });
})();
