document.addEventListener('DOMContentLoaded', function () {
    // Configuration from global object
    const config = window.createOrderConfig || {};

    let currentStep = 1;
    const totalSteps = config.isAuthenticated ? 4 : 5;
    const isAuthenticated = config.isAuthenticated;

    // Form data storage
    let formData = {
        service: null,
        serviceName: '',
        county: '',
        city: '',
        urgency: '',
        title: '',
        description: ''
    };

    // Step navigation functions
    function showStep(step) {
        // Hide all steps
        document.querySelectorAll('.step-content').forEach(content => {
            content.classList.remove('active');
        });

        // Show current step
        document.getElementById(`step-${step}`).classList.add('active');

        // Update step wizard
        document.querySelectorAll('.step').forEach((stepEl, index) => {
            stepEl.classList.remove('active', 'completed');
            if (index + 1 < step) {
                stepEl.classList.add('completed');
            } else if (index + 1 === step) {
                stepEl.classList.add('active');
            }
        });

        currentStep = step;
        updateSummary();
    }

    function nextStep() {
        if (currentStep < totalSteps) {
            showStep(currentStep + 1);
        }
    }

    function prevStep() {
        if (currentStep > 1) {
            showStep(currentStep - 1);
        }
    }

    // Step 1: Two-Level Category → Service Selection
    const servicesByCategory = config.servicesByCategory || {};
    const categorySelection = document.getElementById('category-selection');
    const serviceSelection = document.getElementById('service-selection');
    const servicesGrid = document.getElementById('services-grid');
    const selectedCategoryTitle = document.getElementById('selected-category-title');
    const backToCategoriesBtn = document.getElementById('backToCategoriesBtn');

    // Category selection (Step 1a)
    document.querySelectorAll('#categories-grid .category-card').forEach(card => {
        card.addEventListener('click', function () {
            const categoryId = this.dataset.categoryId;
            const categoryName = this.dataset.categoryName;

            // Load services for this category
            loadServicesForCategory(categoryId, categoryName);
        });
    });

    function loadServicesForCategory(categoryId, categoryName) {
        const services = servicesByCategory[categoryId] || [];

        // Clear previous services
        servicesGrid.innerHTML = '';

        // Populate services
        services.forEach(service => {
            const serviceCard = document.createElement('div');
            serviceCard.className = 'category-card';
            serviceCard.dataset.service = service.id;
            serviceCard.dataset.name = service.name;

            serviceCard.innerHTML = `
                <i class="${service.icon}"></i>
                <p class="category-name">${service.name}</p>
            `;

            // Add click handler for service selection
            serviceCard.addEventListener('click', function () {
                // Remove previous selection
                document.querySelectorAll('#services-grid .category-card').forEach(c => c.classList.remove('selected'));

                // Select current
                this.classList.add('selected');

                // Store data
                formData.service = service.id;
                formData.serviceName = service.name;
                document.getElementById('selected-service').value = service.id;

                // Enable next button
                document.getElementById('step1Next').disabled = false;
            });

            servicesGrid.appendChild(serviceCard);
        });

        // Update title
        selectedCategoryTitle.textContent = categoryName;

        // Show service selection, hide category selection
        categorySelection.style.display = 'none';
        serviceSelection.style.display = 'block';

        // Disable next button until service selected
        document.getElementById('step1Next').disabled = true;
    }

    // Back to categories button
    if (backToCategoriesBtn) {
        backToCategoriesBtn.addEventListener('click', function () {
            categorySelection.style.display = 'block';
            serviceSelection.style.display = 'none';
            document.getElementById('step1Next').disabled = true;
        });
    }

    // For craftsman services (direct selection)
    document.querySelectorAll('#craftsman-services-grid .category-card').forEach(card => {
        card.addEventListener('click', function () {
            // Remove previous selection
            document.querySelectorAll('#craftsman-services-grid .category-card').forEach(c => c.classList.remove('selected'));

            // Select current
            this.classList.add('selected');

            // Store data
            formData.service = this.dataset.service;
            formData.serviceName = this.dataset.name;
            document.getElementById('selected-service').value = formData.service;

            // Enable next button
            document.getElementById('step1Next').disabled = false;
        });
    });

    document.getElementById('step1Next').addEventListener('click', nextStep);

    // Step 2: Location
    const countySelect = document.getElementById(config.countyFieldId);
    const citySelect = document.getElementById(config.cityFieldId);

    function checkStep2Completion() {
        const hasCounty = countySelect.value !== '';
        const hasCity = citySelect.value !== '';
        document.getElementById('step2Next').disabled = !(hasCounty && hasCity);

        if (hasCounty && hasCity) {
            formData.county = countySelect.options[countySelect.selectedIndex].text;
            formData.city = citySelect.options[citySelect.selectedIndex].text;
        }
    }

    if (countySelect && citySelect) {
        countySelect.addEventListener('change', checkStep2Completion);
        citySelect.addEventListener('change', checkStep2Completion);
    }

    document.getElementById('step2Prev').addEventListener('click', prevStep);
    document.getElementById('step2Next').addEventListener('click', nextStep);

    // Step 3: Details
    document.querySelectorAll('.urgency-card').forEach(card => {
        card.addEventListener('click', function () {
            // Remove previous selection
            document.querySelectorAll('.urgency-card').forEach(c => c.classList.remove('selected'));

            // Select current
            this.classList.add('selected');

            // Store data
            formData.urgency = this.dataset.urgency;
            document.getElementById('selected-urgency').value = formData.urgency;

            checkStep3Completion();
        });
    });

    const titleInput = document.getElementById(config.titleFieldId);
    const descriptionInput = document.getElementById(config.descriptionFieldId);

    function checkStep3Completion() {
        const hasTitle = titleInput.value.trim() !== '';
        const hasDescription = descriptionInput.value.trim() !== '';
        const hasUrgency = formData.urgency !== '';

        document.getElementById('step3Next').disabled = !(hasTitle && hasDescription && hasUrgency);

        if (hasTitle) formData.title = titleInput.value;
        if (hasDescription) formData.description = descriptionInput.value;
    }

    if (titleInput) titleInput.addEventListener('input', checkStep3Completion);
    if (descriptionInput) descriptionInput.addEventListener('input', checkStep3Completion);

    document.getElementById('step3Prev').addEventListener('click', prevStep);
    document.getElementById('step3Next').addEventListener('click', nextStep);

    // Step 4: Authentication (Anonymous Users Only)
    if (!isAuthenticated) {
        const userEmailInput = document.getElementById(config.userEmailFieldId);
        const userPhoneInput = document.getElementById(config.userPhoneFieldId);
        const userNameInput = document.getElementById(config.userNameFieldId);
        const userPasswordInput = document.getElementById(config.userPasswordFieldId);
        const userPasswordConfirmInput = document.getElementById(config.userPasswordConfirmFieldId);
        const passwordConfirmField = document.getElementById('password-confirm-field');
        const verificationMethodField = document.getElementById('verification-method-field');
        const existingUserAlert = document.getElementById('existing-user-alert');
        const newUserAlert = document.getElementById('new-user-alert');
        const emailCheckMessage = document.getElementById('email-check-message');

        let userExists = false;
        let checkDebounceTimer;

        // Check if user exists (AJAX)
        function checkUserExists() {
            const email = userEmailInput.value.trim();
            const phone = userPhoneInput.value.trim();

            if (!email && !phone) {
                emailCheckMessage.textContent = '';
                emailCheckMessage.className = 'form-text';
                return;
            }

            clearTimeout(checkDebounceTimer);
            checkDebounceTimer = setTimeout(() => {
                fetch('/api/accounts/check-user/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': config.csrfToken
                    },
                    body: JSON.stringify({ email, phone })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            userExists = true;
                            existingUserAlert.style.display = 'block';
                            newUserAlert.style.display = 'none';
                            passwordConfirmField.style.display = 'none';
                            verificationMethodField.style.display = 'none';
                            emailCheckMessage.textContent = '✅ ' + data.message;
                            emailCheckMessage.className = 'form-text text-success';
                        } else {
                            userExists = false;
                            existingUserAlert.style.display = 'none';
                            newUserAlert.style.display = 'block';
                            passwordConfirmField.style.display = 'block';
                            verificationMethodField.style.display = 'block';
                            emailCheckMessage.textContent = '📝 Cont nou - introduci datele de mai jos';
                            emailCheckMessage.className = 'form-text text-primary';
                        }
                        checkStep4Completion();
                    })
                    .catch(error => {
                        console.error('Error checking user:', error);
                    });
            }, 500);
        }

        if (userEmailInput) userEmailInput.addEventListener('blur', checkUserExists);
        if (userPhoneInput) userPhoneInput.addEventListener('blur', checkUserExists);

        function checkStep4Completion() {
            const hasName = userNameInput.value.trim() !== '';
            const hasEmail = userEmailInput.value.trim() !== '';
            const hasPassword = userPasswordInput.value.trim() !== '';

            let isValid = hasName && hasEmail && hasPassword;

            // If new user, check password confirmation
            if (!userExists && hasPassword) {
                const hasPasswordConfirm = userPasswordConfirmInput.value.trim() !== '';
                const passwordsMatch = userPasswordInput.value === userPasswordConfirmInput.value;
                isValid = isValid && hasPasswordConfirm && passwordsMatch;

                if (hasPasswordConfirm && !passwordsMatch) {
                    userPasswordConfirmInput.setCustomValidity('Parolele nu coincid');
                } else {
                    userPasswordConfirmInput.setCustomValidity('');
                }
            }

            document.getElementById('step4Next').disabled = !isValid;
        }

        if (userNameInput) userNameInput.addEventListener('input', checkStep4Completion);
        if (userEmailInput) userEmailInput.addEventListener('input', checkStep4Completion);
        if (userPasswordInput) userPasswordInput.addEventListener('input', checkStep4Completion);
        if (userPasswordConfirmInput) userPasswordConfirmInput.addEventListener('input', checkStep4Completion);

        document.getElementById('step4Prev').addEventListener('click', prevStep);
        document.getElementById('step4Next').addEventListener('click', nextStep);
    }

    // Photo Upload Functionality
    const photoInput = document.getElementById('photo-input');
    const addPhotosBtn = document.getElementById('add-photos-btn');
    const photoPreviewContainer = document.getElementById('photo-preview-container');
    const uploadArea = document.getElementById('photo-upload-area');
    let uploadedPhotos = [];
    const maxPhotos = 10;

    if (addPhotosBtn) {
        addPhotosBtn.addEventListener('click', () => {
            photoInput.click();
        });
    }

    if (photoInput) {
        photoInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            handlePhotoUpload(files);
        });
    }

    function handlePhotoUpload(files) {
        const validFiles = files.filter(file => {
            const isImage = file.type.startsWith('image/');
            const isValidSize = file.size <= 5 * 1024 * 1024; // 5MB
            return isImage && isValidSize;
        });

        if (uploadedPhotos.length + validFiles.length > maxPhotos) {
            alert(`Poți încărca maximum ${maxPhotos} poze. Ai selectat ${validFiles.length} poze, dar mai poți adăuga doar ${maxPhotos - uploadedPhotos.length}.`);
            return;
        }

        validFiles.forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const photoData = {
                    file: file,
                    url: e.target.result,
                    id: Date.now() + Math.random()
                };

                uploadedPhotos.push(photoData);
                renderPhotoPreview(photoData);
                updateUploadArea();
            };
            reader.readAsDataURL(file);
        });
    }

    function renderPhotoPreview(photoData) {
        const previewItem = document.createElement('div');
        previewItem.className = 'photo-preview-item';
        previewItem.dataset.photoId = photoData.id;

        previewItem.innerHTML = `
            <img src="${photoData.url}" alt="Preview">
            <button type="button" class="photo-remove-btn" onclick="removePhoto(${photoData.id})">
                <i class="fas fa-times"></i>
            </button>
        `;

        photoPreviewContainer.appendChild(previewItem);
    }

    window.removePhoto = function (photoId) {
        uploadedPhotos = uploadedPhotos.filter(photo => photo.id !== photoId);
        const previewItem = document.querySelector(`[data-photo-id="${photoId}"]`);
        if (previewItem) {
            previewItem.remove();
        }
        updateUploadArea();
    };

    function updateUploadArea() {
        if (uploadedPhotos.length >= maxPhotos) {
            uploadArea.style.display = 'none';
        } else {
            uploadArea.style.display = 'block';
            const remaining = maxPhotos - uploadedPhotos.length;
            addPhotosBtn.innerHTML = `<i class="fas fa-plus me-2"></i>Adaugă poze (${remaining} rămase)`;
        }

        if (uploadedPhotos.length > 0) {
            photoPreviewContainer.style.display = 'grid';
        } else {
            photoPreviewContainer.style.display = 'none';
        }
    }

    // Step 5 (or 4 for authenticated): Budget & Summary
    const finalStepPrevBtn = document.getElementById(`step${isAuthenticated ? 4 : 5}Prev`);
    if (finalStepPrevBtn) {
        finalStepPrevBtn.addEventListener('click', prevStep);
    }

    // Update summary
    function updateSummary() {
        const summaryStep = isAuthenticated ? 4 : 5;
        if (currentStep >= summaryStep) {
            document.getElementById('summary-service').textContent = formData.serviceName || '-';
            document.getElementById('summary-location').textContent =
                (formData.county && formData.city) ? `${formData.city}, ${formData.county}` : '-';
            document.getElementById('summary-title').textContent = formData.title || '-';

            let urgencyText = '-';
            if (formData.urgency === 'low') urgencyText = 'Flexibil';
            else if (formData.urgency === 'medium') urgencyText = 'Normal';
            else if (formData.urgency === 'high') urgencyText = 'Urgent';

            document.getElementById('summary-urgency').textContent = urgencyText;
        }
    }

    // Form submission
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function (e) {
            // Ensure all hidden fields are populated
            if (!formData.service || !formData.urgency) {
                e.preventDefault();
                alert('Te rugăm să completezi toate câmpurile obligatorii.');
                return false;
            }

            // Add uploaded photos to form data if any
            if (uploadedPhotos.length > 0) {
                e.preventDefault();

                const formElement = this;
                const formDataObj = new FormData(formElement);

                // Add uploaded photos
                uploadedPhotos.forEach(photoData => {
                    formDataObj.append('images', photoData.file);
                });

                // Get CSRF token from form (not cookie) - more reliable
                const csrftoken = formElement.querySelector('[name=csrfmiddlewaretoken]').value;

                // Submit form with images using fetch
                fetch(formElement.action || window.location.href, {
                    method: 'POST',
                    body: formDataObj,
                    headers: {
                        'X-CSRFToken': csrftoken
                    }
                })
                    .then(response => {
                        if (response.redirected) {
                            // Follow redirect
                            window.location.href = response.url;
                        } else if (response.ok) {
                            // Success but no redirect - manually redirect to my orders page
                            window.location.href = '/servicii/comenzile-mele/';
                        } else {
                            return response.text().then(text => {
                                console.error('Server error:', text);
                                alert('A apărut o eroare la trimiterea comenzii. Verifică datele și încearcă din nou.');
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('A apărut o eroare la trimiterea comenzii. Verifică conexiunea și încearcă din nou.');
                    });
            }
            // If no photos, form submits normally
        });
    }

    // Initialize
    showStep(1);
});
