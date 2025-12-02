document.addEventListener('DOMContentLoaded', function () {
    // Mark notification as read when clicked
    const notificationLinks = document.querySelectorAll('.notification-item-link');

    notificationLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const notificationId = this.dataset.notificationId;
            const actionUrl = this.getAttribute('href');

            // Only mark as read if there's an actual action URL
            if (actionUrl && actionUrl !== '#') {
                // Send mark-as-read request
                fetch(`/notifications/api/notifications/${notificationId}/mark-read/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }).catch(error => {
                    console.error('Error marking notification as read:', error);
                });
            } else {
                e.preventDefault();
            }
        });
    });

    // Get CSRF token from cookie
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
