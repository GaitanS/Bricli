document.addEventListener('DOMContentLoaded', function () {
    // Initialize Lightbox for all review thumbnails
    if (typeof BricliLightbox !== 'undefined') {
        BricliLightbox.init('.review-thumbnail', {
            title: 'Imagini Recenzii',
            showCaption: true,
            initGuardKey: 'craftsmanReviewsLightboxInit'
        });
    }
});
