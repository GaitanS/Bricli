document.addEventListener('DOMContentLoaded', function () {
    // Review Images Lightbox Initialization
    if (typeof BricliLightbox !== 'undefined') {
        BricliLightbox.init('.review-image-thumbnail', {
            title: 'Imagini Recenzie',
            showCaption: true,
            initGuardKey: 'reviewImagesLightboxInit'
        });
    }
});
