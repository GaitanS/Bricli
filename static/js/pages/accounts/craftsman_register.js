let currentStep = 1;
const totalSteps = 3;

function showStep(stepNumber) {
    // Hide all steps
    for (let i = 1; i <= totalSteps; i++) {
        const stepContent = document.getElementById(`step-${i}`);
        const stepItem = document.querySelector(`[data-step="${i}"]`);

        if (stepContent) {
            stepContent.style.display = i === stepNumber ? 'block' : 'none';
        }

        if (stepItem) {
            stepItem.classList.remove('active', 'completed');
            if (i < stepNumber) {
                stepItem.classList.add('completed');
            } else if (i === stepNumber) {
                stepItem.classList.add('active');
            }
        }
    }

    // Update step lines
    const stepLines = document.querySelectorAll('.step-line');
    stepLines.forEach((line, index) => {
        line.classList.toggle('completed', index < stepNumber - 1);
    });

    currentStep = stepNumber;
}

async function nextStep(stepNumber) {
    // Show loading state
    const nextButton = document.querySelector(`#step-${currentStep} button[onclick*="nextStep"]`);
    if (nextButton) {
        nextButton.disabled = true;
        nextButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Verificare...';
    }

    const isValid = await validateCurrentStep();

    // Restore button state
    if (nextButton) {
        nextButton.disabled = false;
        nextButton.innerHTML = 'Următorul pas <i class="fas fa-arrow-right ms-2"></i>';
    }

    if (isValid) {
        showStep(stepNumber);
    }
}

function prevStep(stepNumber) {
    showStep(stepNumber);
}

async function validateCurrentStep() {
    const currentStepElement = document.getElementById(`step-${currentStep}`);
    const requiredFields = currentStepElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;

    // Basic required field validation
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            showFieldError(field, 'Acest câmp este obligatoriu.');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            hideFieldError(field);
        }
    });

    // Special validation for step 1
    if (currentStep === 1) {
        // Password match validation
        const password = document.querySelector('input[name="password"]');
        const passwordConfirm = document.querySelector('input[name="password_confirm"]');

        if (password && passwordConfirm && password.value !== passwordConfirm.value) {
            passwordConfirm.classList.add('is-invalid');
            showFieldError(passwordConfirm, 'Parolele nu se potrivesc.');
            isValid = false;
        }

        // AJAX validation for email and phone
        const emailField = document.querySelector('input[name="email"]');
        const phoneField = document.querySelector('input[name="phone_number"]');

        if (emailField && emailField.value.trim()) {
            const emailValid = await validateEmailAjax(emailField.value);
            if (!emailValid.valid) {
                emailField.classList.add('is-invalid');
                showFieldError(emailField, emailValid.message);
                isValid = false;
            } else {
                emailField.classList.remove('is-invalid');
                hideFieldError(emailField);
            }
        }

        if (phoneField && phoneField.value.trim()) {
            const phoneValid = await validatePhoneAjax(phoneField.value);
            if (!phoneValid.valid) {
                phoneField.classList.add('is-invalid');
                showFieldError(phoneField, phoneValid.message);
                isValid = false;
            } else {
                phoneField.classList.remove('is-invalid');
                hideFieldError(phoneField);
            }
        }
    }

    // Special validation for step 2 (bio length)
    if (currentStep === 2) {
        const bioField = document.querySelector('textarea[name="bio"]');
        if (bioField) {
            const bioText = bioField.value.trim();
            if (bioText.length < 200) {
                bioField.classList.add('is-invalid');
                showFieldError(bioField, `Biografia trebuie să aibă cel puțin 200 caractere. Ai scris ${bioText.length} caractere.`);
                isValid = false;
            } else {
                bioField.classList.remove('is-invalid');
                hideFieldError(bioField);
            }
        }
    }

    // Special validation for step 3 (at least one service selected)
    if (currentStep === 3) {
        const selectedServices = document.querySelectorAll('.service-checkbox:checked');
        if (selectedServices.length === 0) {
            alert('Te rugăm să selectezi cel puțin un serviciu.');
            isValid = false;
        }
    }

    return isValid;
}

async function validateEmailAjax(email) {
    try {
        const response = await fetch('/accounts/api/validate-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `email=${encodeURIComponent(email)}`
        });
        return await response.json();
    } catch (error) {
        console.error('Email validation error:', error);
        return { valid: true, message: '' }; // Fallback to allow progression
    }
}

async function validatePhoneAjax(phone) {
    try {
        const response = await fetch('/accounts/api/validate-phone/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `phone=${encodeURIComponent(phone)}`
        });
        return await response.json();
    } catch (error) {
        console.error('Phone validation error:', error);
        return { valid: true, message: '' }; // Fallback to allow progression
    }
}

function showFieldError(field, message) {
    // Remove existing error message
    hideFieldError(field);

    // Create and show new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-danger small mt-1 field-error';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function hideFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const serviceCheckboxes = document.querySelectorAll('.service-checkbox');
    const selectedCountSpan = document.getElementById('selected-count');
    const serviceSearch = document.getElementById('service-search');
    const clearSearchBtn = document.getElementById('clear-search');
    const maxServices = 10;

    // Initialize first step
    showStep(1);

    // Add real-time validation for email and phone
    const emailField = document.querySelector('input[name="email"]');
    const phoneField = document.querySelector('input[name="phone_number"]');

    if (emailField) {
        emailField.addEventListener('blur', async function () {
            if (this.value.trim()) {
                const result = await validateEmailAjax(this.value);
                if (!result.valid) {
                    this.classList.add('is-invalid');
                    showFieldError(this, result.message);
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    hideFieldError(this);
                }
            }
        });
    }

    if (phoneField) {
        phoneField.addEventListener('blur', async function () {
            if (this.value.trim()) {
                const result = await validatePhoneAjax(this.value);
                if (!result.valid) {
                    this.classList.add('is-invalid');
                    showFieldError(this, result.message);
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    hideFieldError(this);
                }
            }
        });
    }

    function updateSelectedCount() {
        const checkedBoxes = document.querySelectorAll('.service-checkbox:checked');
        const count = checkedBoxes.length;

        selectedCountSpan.textContent = count;

        // Disable unchecked boxes if max reached
        serviceCheckboxes.forEach(checkbox => {
            if (!checkbox.checked && count >= maxServices) {
                checkbox.disabled = true;
                checkbox.parentElement.classList.add('text-muted');
            } else if (count < maxServices) {
                checkbox.disabled = false;
                checkbox.parentElement.classList.remove('text-muted');
            }
        });

        // Update color based on count
        if (count === 0) {
            selectedCountSpan.className = 'text-muted';
        } else if (count <= maxServices) {
            selectedCountSpan.className = 'text-success';
        } else {
            selectedCountSpan.className = 'text-danger';
        }
    }

    // Search functionality
    function filterServices() {
        const searchTerm = serviceSearch.value.toLowerCase().trim();
        const serviceItems = document.querySelectorAll('.service-item');
        const categoryTitles = document.querySelectorAll('.category-title');
        const categorySections = document.querySelectorAll('.category-section');

        // Show/hide clear button
        clearSearchBtn.style.display = searchTerm ? 'inline-block' : 'none';

        if (searchTerm === '') {
            // Show all services and categories
            serviceItems.forEach(item => item.style.display = 'block');
            categorySections.forEach(section => section.style.display = 'block');
            return;
        }

        // Filter services
        serviceItems.forEach(item => {
            const serviceName = item.getAttribute('data-service-name');
            const categoryName = item.getAttribute('data-category');

            if ((serviceName && serviceName.includes(searchTerm)) ||
                (categoryName && categoryName.includes(searchTerm))) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });

        // Show/hide category sections based on visible services
        categorySections.forEach(section => {
            const visibleServices = section.querySelectorAll('.service-item[style="display: block"], .service-item:not([style*="display: none"])');
            section.style.display = visibleServices.length > 0 ? 'block' : 'none';
        });
    }

    function clearSearch() {
        serviceSearch.value = '';
        filterServices();
        serviceSearch.focus();
    }

    // Add event listeners to all checkboxes
    serviceCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });

    // Initialize count
    updateSelectedCount();

    // Search event listeners
    if (serviceSearch) {
        serviceSearch.addEventListener('input', filterServices);
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', clearSearch);
    }
});
