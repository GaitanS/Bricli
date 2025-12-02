document.addEventListener('DOMContentLoaded', function () {
    // Rating descriptions
    const ratingDescriptions = {
        1: {
            text: '⭐ Nesatisfăcător',
            description: 'Experiență foarte slabă, probleme majore cu lucrarea sau meșterul.',
            badge: 'rating-badge-1'
        },
        2: {
            text: '⭐⭐ Sub așteptări',
            description: 'Experiență mediocră, mai multe probleme decât aspecte pozitive.',
            badge: 'rating-badge-2'
        },
        3: {
            text: '⭐⭐⭐ Acceptabil',
            description: 'Experiență medie, lucrarea este acceptabilă dar cu îmbunătățiri necesare.',
            badge: 'rating-badge-3'
        },
        4: {
            text: '⭐⭐⭐⭐ Foarte bun',
            description: 'Experiență foarte bună, lucrare de calitate cu mici aspecte de îmbunătățit.',
            badge: 'rating-badge-4'
        },
        5: {
            text: '⭐⭐⭐⭐⭐ Excelent',
            description: 'Experiență excepțională! Lucrare impecabilă, profesionalism maxim.',
            badge: 'rating-badge-5'
        }
    };

    // Smart Guide System
    const smartGuideBanner = document.getElementById('smartGuideBanner');
    const dismissGuideBtn = document.getElementById('dismissGuide');
    const ratingGuideBtn = document.getElementById('ratingGuideBtn');

    // Check if user has dismissed guide before
    const hasSeenGuide = localStorage.getItem('bricli_review_guide_seen');

    if (hasSeenGuide) {
        smartGuideBanner.style.display = 'none';
    }

    dismissGuideBtn.addEventListener('click', function () {
        smartGuideBanner.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => {
            smartGuideBanner.style.display = 'none';
        }, 300);
        localStorage.setItem('bricli_review_guide_seen', 'true');
    });

    ratingGuideBtn.addEventListener('click', function () {
        smartGuideBanner.style.display = 'block';
        smartGuideBanner.style.animation = 'slideDown 0.5s ease';
        smartGuideBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });

    // Overall Rating Stars
    const overallStars = document.querySelector('.overall-stars');
    if (overallStars) {
        const stars = overallStars.querySelectorAll('.hover-star-large');
        const radioInputs = overallStars.querySelectorAll('input[type="radio"]');
        const ratingDescription = document.getElementById('ratingDescription');

        // Initialize with existing selection
        const checkedInput = overallStars.querySelector('input[type="radio"]:checked');
        if (checkedInput) {
            const value = parseInt(checkedInput.value);
            updateOverallStars(stars, value);
            updateRatingDescription(value);
        }

        // Hover effect
        stars.forEach((star, index) => {
            star.addEventListener('mouseenter', function () {
                const value = parseInt(this.dataset.value);
                updateOverallStars(stars, value);
                updateRatingDescription(value, true);
            });

            // Click to select
            star.addEventListener('click', function () {
                const value = parseInt(this.dataset.value);

                // Update radio input
                radioInputs.forEach(input => {
                    if (parseInt(input.value) === value) {
                        input.checked = true;
                    }
                });

                // Update visual stars with animation
                updateOverallStars(stars, value);
                updateRatingDescription(value);

                // Add bounce animation
                stars.forEach((s, i) => {
                    if (i < value) {
                        s.classList.add('active');
                        setTimeout(() => s.classList.remove('active'), 600);
                    }
                });

                // Scroll to next section after selection
                setTimeout(() => {
                    document.querySelector('.detailed-rating-row').scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 800);
            });
        });

        // Reset on mouse leave
        overallStars.addEventListener('mouseleave', function () {
            const checkedInput = overallStars.querySelector('input[type="radio"]:checked');
            if (checkedInput) {
                const value = parseInt(checkedInput.value);
                updateOverallStars(stars, value);
                updateRatingDescription(value);
            } else {
                updateOverallStars(stars, 0);
                ratingDescription.innerHTML = '<i class="fas fa-hand-pointer me-2" style="color: #8B5CF6;"></i><span class="text-muted">Selectează un rating pentru a continua</span>';
                ratingDescription.classList.remove('active');
            }
        });

        function updateOverallStars(stars, value) {
            stars.forEach((star, index) => {
                if (index < value) {
                    star.classList.remove('far');
                    star.classList.add('fas', 'filled');
                } else {
                    star.classList.remove('fas', 'filled');
                    star.classList.add('far');
                }
            });
        }

        function updateRatingDescription(value, isHover = false) {
            if (value && ratingDescriptions[value]) {
                const desc = ratingDescriptions[value];
                ratingDescription.innerHTML = `
                    <div>
                        <div class="rating-badge ${desc.badge} mb-2">
                            ${desc.text}
                        </div>
                        <div class="small text-muted">
                            ${isHover ? '<i class="fas fa-mouse-pointer me-1"></i> Click pentru a selecta - ' : ''}${desc.description}
                        </div>
                    </div>
                `;
                ratingDescription.classList.add('active');
            }
        }
    }

    // Hover star rating functionality for detailed ratings
    const hoverRatingContainers = document.querySelectorAll('.hover-star-rating:not(.overall-stars)');

    hoverRatingContainers.forEach(container => {
        const stars = container.querySelectorAll('.hover-star');
        const ratingName = container.dataset.ratingName;
        const radioInputs = container.querySelectorAll('input[type="radio"]');

        // Initialize with existing selection
        const checkedInput = container.querySelector('input[type="radio"]:checked');
        if (checkedInput) {
            const value = parseInt(checkedInput.value);
            updateStars(stars, value, true);
        }

        // Hover effect
        stars.forEach((star, index) => {
            star.addEventListener('mouseenter', function () {
                const value = parseInt(this.dataset.value);
                updateStars(stars, value, false);
            });

            // Click to select
            star.addEventListener('click', function () {
                const value = parseInt(this.dataset.value);

                // Update radio input
                radioInputs.forEach(input => {
                    if (parseInt(input.value) === value) {
                        input.checked = true;
                    }
                });

                // Update visual stars with animation
                updateStars(stars, value, true);

                // Add bounce animation
                stars.forEach((s, i) => {
                    if (i < value) {
                        s.classList.add('active');
                        setTimeout(() => s.classList.remove('active'), 500);
                    }
                });
            });
        });

        // Reset on mouse leave
        container.addEventListener('mouseleave', function () {
            const checkedInput = container.querySelector('input[type="radio"]:checked');
            if (checkedInput) {
                const value = parseInt(checkedInput.value);
                updateStars(stars, value, true);
            } else {
                updateStars(stars, 0, false);
            }
        });
    });

    function updateStars(stars, value, permanent) {
        stars.forEach((star, index) => {
            if (index < value) {
                star.classList.remove('far');
                star.classList.add('fas', 'filled');
            } else {
                star.classList.remove('fas', 'filled');
                star.classList.add('far');
            }
        });
    }

    // Character counter for comment
    const commentField = document.getElementById('id_comment');
    if (commentField) {
        commentField.addEventListener('input', function () {
            const length = this.value.length;
            const maxLength = 1000;
            console.log(`Characters: ${length}/${maxLength}`);
        });
    }

    // Form validation enhancement
    const form = document.getElementById('reviewForm');
    form.addEventListener('submit', function (e) {
        const ratingSelected = document.querySelector('.overall-stars input[type="radio"]:checked');
        if (!ratingSelected) {
            e.preventDefault();
            alert('Te rugăm să selectezi un rating general!');
            document.querySelector('.overall-rating-container').scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });

    // ===== IMAGE UPLOAD HANDLER =====
    const imageInput = document.getElementById('reviewImages');
    if (imageInput) {
        const previewContainer = document.getElementById('imagePreviewContainer');
        const uploadStats = document.getElementById('uploadStats');
        const selectedCountEl = document.getElementById('selectedCount');
        const clearAllBtn = document.getElementById('clearAll');
        const uploadTrigger = document.getElementById('uploadTrigger');

        const maxImages = parseInt(imageInput.dataset.max) || 5;
        let selectedFiles = [];

        // Handle file selection
        imageInput.addEventListener('change', function (e) {
            const files = Array.from(e.target.files);
            handleFiles(files);
        });

        // Clear all button
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', function () {
                selectedFiles = [];
                updatePreview();
                imageInput.value = '';
            });
        }

        function handleFiles(files) {
            // Filter and validate
            const validFiles = files.filter(file => {
                // Check if image
                if (!file.type.startsWith('image/')) {
                    alert(`Fișierul "${file.name}" nu este o imagine validă.`);
                    return false;
                }

                // Check size (5MB)
                const maxSize = 5 * 1024 * 1024;
                if (file.size > maxSize) {
                    alert(`Imaginea "${file.name}" este prea mare (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maxim 5MB.`);
                    return false;
                }

                return true;
            });

            // Check total count
            if (selectedFiles.length + validFiles.length > maxImages) {
                alert(`Poți adăuga maximum ${maxImages} imagini. Ai selectat ${selectedFiles.length + validFiles.length}.`);
                return;
            }

            // Add to selected files
            selectedFiles = [...selectedFiles, ...validFiles];
            updatePreview();
            updateFileInput();
        }

        function updatePreview() {
            if (selectedFiles.length === 0) {
                previewContainer.style.display = 'none';
                uploadStats.style.display = 'none';
                uploadTrigger.style.display = 'block';
                return;
            }

            previewContainer.style.display = 'grid';
            uploadStats.style.display = 'block';
            uploadTrigger.style.display = 'none';
            previewContainer.innerHTML = '';

            selectedFiles.forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const card = document.createElement('div');
                    card.className = 'preview-card';
                    card.innerHTML = `
                        <img src="${e.target.result}" alt="Preview ${index + 1}" class="preview-image">
                        <div class="preview-overlay">
                            <span class="preview-badge">#${index + 1}</span>
                            <button type="button" class="preview-remove" data-index="${index}">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div class="preview-info">
                            <p class="preview-filename" title="${file.name}">${file.name}</p>
                            <small class="preview-filesize">${(file.size / 1024).toFixed(1)} KB</small>
                        </div>
                    `;

                    // Remove button handler
                    const removeBtn = card.querySelector('.preview-remove');
                    removeBtn.addEventListener('click', function () {
                        removeFile(parseInt(this.dataset.index));
                    });

                    previewContainer.appendChild(card);
                };
                reader.readAsDataURL(file);
            });

            // Update stats
            selectedCountEl.textContent = `${selectedFiles.length} ${selectedFiles.length === 1 ? 'imagine selectată' : 'imagini selectate'}`;
        }

        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updatePreview();
            updateFileInput();
        }

        function updateFileInput() {
            // Create new DataTransfer to update input files
            const dataTransfer = new DataTransfer();
            selectedFiles.forEach(file => {
                dataTransfer.items.add(file);
            });
            imageInput.files = dataTransfer.files;
        }
    }
});
