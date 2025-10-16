/**
 * Bricli Universal Image Lightbox
 * Features: Zoom (100-200%), Pan/Drag, Navigation (←/→), Keyboard Shortcuts
 *
 * Usage:
 *   BricliLightbox.init('.gallery-image', {
 *     title: 'Portfolio',
 *     showCaption: true
 *   });
 */

window.BricliLightbox = (function() {
    'use strict';

    class ImageLightbox {
        constructor(imageSelector, options = {}) {
            this.imageSelector = imageSelector;
            this.options = {
                title: options.title || 'Imagine',
                showCaption: options.showCaption !== false,
                initGuardKey: options.initGuardKey || 'bricliLightboxInitialized',
                ...options
            };

            // Prevent multiple initializations
            if (window[this.options.initGuardKey]) {
                console.warn('BricliLightbox already initialized with key:', this.options.initGuardKey);
                return;
            }
            window[this.options.initGuardKey] = true;

            // State
            this.images = [];
            this.currentIndex = 0;
            this.modal = null;
            this.zoomLevel = 1;
            this.translateX = 0;
            this.translateY = 0;
            this.isPanning = false;
            this.startX = 0;
            this.startY = 0;

            // Constants
            this.MIN_ZOOM = 1;
            this.MAX_ZOOM = 2;
            this.ZOOM_STEP = 0.5;

            this.init();
        }

        init() {
            // Get DOM elements
            this.lightbox = document.getElementById('imageLightbox');
            this.lightboxImage = document.getElementById('lightboxImage');
            this.imageContainer = document.getElementById('lightboxImageContainer');
            this.prevBtn = document.getElementById('lightboxPrevBtn');
            this.nextBtn = document.getElementById('lightboxNextBtn');
            this.counterEl = document.getElementById('lightboxCounter');
            this.captionEl = document.getElementById('lightboxCaption');
            this.titleEl = document.getElementById('lightboxTitle');
            this.zoomInBtn = document.getElementById('lightboxZoomIn');
            this.zoomOutBtn = document.getElementById('lightboxZoomOut');
            this.zoomResetBtn = document.getElementById('lightboxZoomReset');

            if (!this.lightbox) {
                console.error('BricliLightbox: Modal element #imageLightbox not found. Include partials/image_lightbox.html');
                return;
            }

            // Collect images
            this.collectImages();

            if (this.images.length === 0) {
                console.warn('BricliLightbox: No images found with selector:', this.imageSelector);
                return;
            }

            // Bind events
            this.bindEvents();
        }

        collectImages() {
            const imageElements = document.querySelectorAll(this.imageSelector);
            this.images = Array.from(imageElements).map((img, index) => ({
                url: img.getAttribute('src'),
                alt: img.getAttribute('alt') || '',
                title: img.getAttribute('data-title') || img.getAttribute('alt') || '',
                index: index,
                element: img
            }));

            // Add click handlers to image elements
            imageElements.forEach((img, idx) => {
                img.style.cursor = 'pointer';
                img.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.openLightbox(idx);
                });
            });
        }

        bindEvents() {
            // Navigation buttons
            if (this.prevBtn) {
                this.prevBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.navigate(-1);
                });
            }

            if (this.nextBtn) {
                this.nextBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.navigate(1);
                });
            }

            // Zoom controls
            if (this.zoomInBtn) {
                this.zoomInBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.zoomIn();
                });
            }

            if (this.zoomOutBtn) {
                this.zoomOutBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.zoomOut();
                });
            }

            if (this.zoomResetBtn) {
                this.zoomResetBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.resetZoom();
                });
            }

            // Pan/drag functionality
            this.lightboxImage.addEventListener('mousedown', (e) => this.startPan(e));
            document.addEventListener('mousemove', (e) => this.doPan(e));
            document.addEventListener('mouseup', () => this.endPan());

            // Keyboard navigation
            document.addEventListener('keydown', (e) => this.handleKeyboard(e));

            // Cleanup on modal close
            this.lightbox.addEventListener('hidden.bs.modal', () => this.cleanup());

            // Initialize zoom buttons state
            this.updateZoomButtons();
        }

        openLightbox(index) {
            this.updateImage(index);
            if (!this.modal) {
                this.modal = new bootstrap.Modal(this.lightbox, {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                });
            }
            this.modal.show();
        }

        updateImage(index) {
            // Wrap around
            if (index < 0) index = this.images.length - 1;
            if (index >= this.images.length) index = 0;
            this.currentIndex = index;

            const img = this.images[this.currentIndex];
            this.lightboxImage.src = img.url;
            this.lightboxImage.alt = img.alt;

            // Update counter
            if (this.counterEl) {
                this.counterEl.textContent = `${this.currentIndex + 1} / ${this.images.length}`;
            }

            // Update caption
            if (this.captionEl && this.options.showCaption) {
                this.captionEl.textContent = img.title;
            }

            // Update title
            if (this.titleEl) {
                this.titleEl.textContent = this.options.title;
            }

            // Reset zoom when changing images
            this.resetZoom();

            // Update navigation button visibility
            if (this.prevBtn) {
                this.prevBtn.style.display = this.images.length > 1 ? 'block' : 'none';
            }
            if (this.nextBtn) {
                this.nextBtn.style.display = this.images.length > 1 ? 'block' : 'none';
            }
        }

        navigate(direction) {
            this.updateImage(this.currentIndex + direction);
        }

        // Zoom functions
        zoomIn() {
            if (this.zoomLevel < this.MAX_ZOOM) {
                this.zoomLevel = Math.min(this.zoomLevel + this.ZOOM_STEP, this.MAX_ZOOM);
                this.applyTransform();
            }
        }

        zoomOut() {
            if (this.zoomLevel > this.MIN_ZOOM) {
                this.zoomLevel = Math.max(this.zoomLevel - this.ZOOM_STEP, this.MIN_ZOOM);
                this.applyTransform();
            }
        }

        resetZoom() {
            this.zoomLevel = 1;
            this.translateX = 0;
            this.translateY = 0;
            this.applyTransform();
        }

        applyTransform() {
            this.lightboxImage.style.transform = `scale(${this.zoomLevel}) translate(${this.translateX}px, ${this.translateY}px)`;
            this.lightboxImage.style.cursor = this.zoomLevel > 1 ? 'grab' : 'default';
            this.updateZoomButtons();
        }

        updateZoomButtons() {
            if (this.zoomOutBtn) {
                this.zoomOutBtn.disabled = this.zoomLevel <= this.MIN_ZOOM;
            }
            if (this.zoomInBtn) {
                this.zoomInBtn.disabled = this.zoomLevel >= this.MAX_ZOOM;
            }
        }

        // Pan functions
        startPan(e) {
            if (this.zoomLevel > 1) {
                this.isPanning = true;
                this.startX = e.clientX - this.translateX;
                this.startY = e.clientY - this.translateY;
                this.lightboxImage.style.cursor = 'grabbing';
                e.preventDefault();
            }
        }

        doPan(e) {
            if (this.isPanning) {
                this.translateX = e.clientX - this.startX;
                this.translateY = e.clientY - this.startY;
                this.applyTransform();
            }
        }

        endPan() {
            if (this.isPanning) {
                this.isPanning = false;
                this.lightboxImage.style.cursor = this.zoomLevel > 1 ? 'grab' : 'default';
            }
        }

        // Keyboard navigation
        handleKeyboard(e) {
            // Only handle keys when modal is visible
            if (!this.lightbox || !this.lightbox.classList.contains('show')) return;

            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.navigate(-1);
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                this.navigate(1);
            } else if (e.key === '+' || e.key === '=') {
                e.preventDefault();
                this.zoomIn();
            } else if (e.key === '-' || e.key === '_') {
                e.preventDefault();
                this.zoomOut();
            } else if (e.key === '0' || e.key === 'r' || e.key === 'R') {
                e.preventDefault();
                this.resetZoom();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                if (this.modal) this.modal.hide();
            }
        }

        cleanup() {
            this.lightboxImage.src = '';
            this.resetZoom();
        }
    }

    // Public API
    return {
        /**
         * Initialize lightbox for image selector
         * @param {string} selector - CSS selector for images (e.g., '.gallery-image')
         * @param {object} options - Configuration options
         * @returns {ImageLightbox} Lightbox instance
         */
        init: function(selector, options = {}) {
            return new ImageLightbox(selector, options);
        }
    };
})();
