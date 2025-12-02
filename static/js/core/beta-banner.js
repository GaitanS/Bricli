/**
 * Beta Banner Dismissal Logic
 * Handles the dismissal and persistence of the beta banner state.
 */
document.addEventListener('DOMContentLoaded', function() {
    const banner = document.getElementById('beta-banner');
    const closeBtn = banner?.querySelector('.btn-close');

    // Check if banner was dismissed recently
    const dismissedTime = localStorage.getItem('beta_banner_dismissed');
    if (dismissedTime) {
        const daysSince = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
        if (daysSince < 7) {
            // Still within 7 days - hide banner
            if (banner) {
                banner.remove();
            }
        }
    }

    // Save dismissal time when close button clicked
    closeBtn?.addEventListener('click', function() {
        localStorage.setItem('beta_banner_dismissed', Date.now().toString());
    });
});
