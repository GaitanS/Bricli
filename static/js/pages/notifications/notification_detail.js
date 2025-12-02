document.addEventListener('DOMContentLoaded', function () {
    // Initialize notification manager
    const notificationManager = new NotificationManager();
    const notificationContainer = document.querySelector('.notification-detail-container');

    if (notificationContainer) {
        const notificationId = notificationContainer.dataset.notificationId;
        const autoMarkRead = notificationContainer.dataset.autoMarkRead === 'true';
        const listUrl = notificationContainer.dataset.listUrl;

        // Mark as read when viewing (if not already read)
        if (autoMarkRead) {
            notificationManager.toggleReadStatus(notificationId, true);
        }

        // Toggle read status
        document.addEventListener('click', function (e) {
            if (e.target.closest('.toggle-read-btn')) {
                const btn = e.target.closest('.toggle-read-btn');
                const btnNotificationId = btn.dataset.notificationId;
                const isRead = btn.dataset.isRead === 'true';

                notificationManager.toggleReadStatus(btnNotificationId, !isRead)
                    .then(() => {
                        // Update button state
                        btn.dataset.isRead = (!isRead).toString();
                        const icon = btn.querySelector('i');

                        if (!isRead) {
                            icon.className = 'fas fa-envelope';
                            btn.title = 'Marchează ca necitită';
                            showToast('Notificarea a fost marcată ca citită.', 'success');
                        } else {
                            icon.className = 'fas fa-envelope-open';
                            btn.title = 'Marchează ca citită';
                            showToast('Notificarea a fost marcată ca necitită.', 'info');
                        }
                    });
            }
        });

        // Delete notification
        document.addEventListener('click', function (e) {
            if (e.target.closest('.delete-btn')) {
                const btn = e.target.closest('.delete-btn');
                const btnNotificationId = btn.dataset.notificationId;

                if (confirm('Sigur doriți să ștergeți această notificare?')) {
                    notificationManager.deleteNotification(btnNotificationId)
                        .then(() => {
                            showToast('Notificarea a fost ștearsă.', 'success');
                            // Redirect to notifications list after 2 seconds
                            if (listUrl) {
                                setTimeout(() => {
                                    window.location.href = listUrl;
                                }, 2000);
                            }
                        });
                }
            }
        });

        // Expandable content functionality
        document.addEventListener('click', function (e) {
            if (e.target.classList.contains('expand-btn')) {
                const container = e.target.closest('.expandable-content');
                const preview = container.querySelector('.content-preview');
                const full = container.querySelector('.content-full');

                preview.classList.add('d-none');
                full.classList.remove('d-none');
            }

            if (e.target.classList.contains('collapse-btn')) {
                const container = e.target.closest('.expandable-content');
                const preview = container.querySelector('.content-preview');
                const full = container.querySelector('.content-full');

                full.classList.add('d-none');
                preview.classList.remove('d-none');
            }
        });
    }
});

function showToast(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    if (!toast) return;

    const toastBody = toast.querySelector('.toast-body');

    // Update toast content
    if (toastBody) toastBody.textContent = message;

    // Update toast style based on type
    toast.className = `toast bg-${type === 'error' ? 'danger' : type} text-white`;

    // Show toast
    if (typeof bootstrap !== 'undefined') {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}
