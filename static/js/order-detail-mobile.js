/**
 * Order Detail Mobile Interactions
 * Features: Carousel swipe, collapsible sections, phone reveal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on mobile
    if (window.innerWidth >= 768) return;

    // ============================================
    // IMAGE CAROUSEL with Swipe Gestures
    // ============================================
    const carousel = document.querySelector('.carousel-track');
    const dots = document.querySelectorAll('.carousel-dot');

    if (carousel && dots.length > 0) {
        let currentIndex = 0;
        let startX = 0;
        let isDragging = false;

        // Touch start
        carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            carousel.style.transition = 'none';
        });

        // Touch move
        carousel.addEventListener('touchmove', (e) => {
            if (!isDragging) return;

            const currentX = e.touches[0].clientX;
            const diff = currentX - startX;
            const offset = currentIndex * -100;
            const newOffset = offset + (diff / carousel.offsetWidth * 100);

            carousel.style.transform = `translateX(${newOffset}%)`;
        });

        // Touch end
        carousel.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            isDragging = false;

            const endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            const threshold = 50; // Minimum swipe distance in pixels

            carousel.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

            if (Math.abs(diff) > threshold) {
                if (diff > 0 && currentIndex < dots.length - 1) {
                    // Swipe left - next image
                    currentIndex++;
                } else if (diff < 0 && currentIndex > 0) {
                    // Swipe right - previous image
                    currentIndex--;
                }
            }

            updateCarousel();
        });

        // Dot click navigation
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                currentIndex = index;
                updateCarousel();
            });
        });

        function updateCarousel() {
            const offset = currentIndex * -100;
            carousel.style.transform = `translateX(${offset}%)`;

            // Update dots
            dots.forEach((dot, index) => {
                if (index === currentIndex) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
        }

        // Initialize
        updateCarousel();
    }

    // ============================================
    // COLLAPSIBLE SECTIONS (Accordion)
    // ============================================
    const sectionToggles = document.querySelectorAll('.section-toggle');

    sectionToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const isOpen = content.classList.contains('show');

            // Close all other sections (optional - remove for multi-open)
            // sectionToggles.forEach(t => {
            //     if (t !== toggle) {
            //         t.classList.remove('active');
            //         t.nextElementSibling.classList.remove('show');
            //     }
            // });

            // Toggle current section
            if (isOpen) {
                this.classList.remove('active');
                content.classList.remove('show');
                content.style.display = 'none';
            } else {
                this.classList.add('active');
                content.classList.add('show');
                content.style.display = 'block';

                // Smooth scroll to section after opening
                setTimeout(() => {
                    this.scrollIntoView({
                        behavior: 'smooth',
                        block: 'nearest'
                    });
                }, 300);
            }
        });
    });

    // ============================================
    // PHONE REVEAL Button
    // ============================================
    const revealPhoneBtn = document.querySelector('.reveal-phone-btn');

    if (revealPhoneBtn && !revealPhoneBtn.classList.contains('revealed')) {
        revealPhoneBtn.addEventListener('click', function() {
            const phone = this.dataset.phone;

            if (phone) {
                // Animate button
                this.style.transform = 'scale(0.95)';

                setTimeout(() => {
                    this.innerHTML = `<i class="fas fa-phone"></i> ${phone}`;
                    this.classList.add('revealed');
                    this.disabled = true;
                    this.style.transform = 'scale(1)';

                    // Make it a phone link
                    const wrapper = document.createElement('a');
                    wrapper.href = `tel:${phone}`;
                    wrapper.className = this.className;
                    wrapper.innerHTML = this.innerHTML;
                    this.parentNode.replaceChild(wrapper, this);
                }, 200);
            }
        });
    }

    // ============================================
    // FAVORITE BUTTON Toggle
    // ============================================
    const favoriteBtn = document.querySelector('.favorite-btn');

    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', function() {
            this.classList.toggle('active');

            // Add bounce animation
            this.style.transform = 'scale(1.2)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);

            // Optional: Send AJAX request to save favorite
            // fetch('/api/favorites/', { method: 'POST', ... })
        });
    }

    // ============================================
    // QUOTE CARD "Vezi mai mult" Button
    // ============================================
    const quoteViewMoreBtns = document.querySelectorAll('.btn-xs.secondary');

    quoteViewMoreBtns.forEach(btn => {
        if (btn.textContent.includes('Vezi mai mult')) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const card = this.closest('.quote-card-mobile');
                const shortDesc = card.querySelector('.quote-description-short');
                const fullDesc = card.dataset.fullDescription;

                if (fullDesc) {
                    shortDesc.style.webkitLineClamp = 'unset';
                    shortDesc.textContent = fullDesc;
                    this.textContent = 'Vezi mai puțin';
                } else {
                    // Toggle back
                    shortDesc.style.webkitLineClamp = '2';
                    this.textContent = 'Vezi mai mult';
                }
            });
        }
    });

    // ============================================
    // PREVENT BODY SCROLL when dragging carousel
    // ============================================
    let isCarouselDragging = false;

    if (carousel) {
        carousel.addEventListener('touchstart', () => {
            isCarouselDragging = true;
        });

        carousel.addEventListener('touchend', () => {
            isCarouselDragging = false;
        });

        document.body.addEventListener('touchmove', (e) => {
            if (isCarouselDragging) {
                e.preventDefault();
            }
        }, { passive: false });
    }

    // ============================================
    // SMOOTH SCROLL to Anchor Links
    // ============================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
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

    // ============================================
    // AUTO-EXPAND First Section (Optional)
    // ============================================
    // Uncomment to auto-open description on load
    // const firstToggle = document.querySelector('.section-toggle');
    // if (firstToggle) {
    //     firstToggle.click();
    // }

    // ============================================
    // LOADING STATE for Action Buttons
    // ============================================
    const actionButtons = document.querySelectorAll('.action-btn-mobile');

    actionButtons.forEach(btn => {
        // Skip phone call buttons
        if (!btn.href || !btn.href.startsWith('tel:')) {
            btn.addEventListener('click', function() {
                const originalHTML = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Se încarcă...';
                this.style.pointerEvents = 'none';

                // Reset after 2 seconds (form submission will navigate away anyway)
                setTimeout(() => {
                    this.innerHTML = originalHTML;
                    this.style.pointerEvents = 'auto';
                }, 2000);
            });
        }
    });

    // ============================================
    // VIEWPORT HEIGHT FIX for Mobile Browsers
    // ============================================
    function setVH() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);

    console.log('📱 Mobile Order Detail initialized');
});
