document.addEventListener('DOMContentLoaded', function () {
    // Initialize notification functionality
    const notificationManager = new NotificationManager();

    // Mark all as read
    const markAllReadBtn = document.getElementById('mark-all-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function () {
            if (confirm('Sigur doriți să marcați toate notificările ca citite?')) {
                notificationManager.markAllAsRead();
            }
        });
    }

    // Select all checkboxes
    const selectAllBtn = document.getElementById('select-all');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function () {
            const checkboxes = document.querySelectorAll('.notification-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);

            checkboxes.forEach(cb => {
                cb.checked = !allChecked;
            });

            this.textContent = allChecked ? 'Selectează toate' : 'Deselectează toate';
            updateBulkDeleteButton();
        });
    }

    // Bulk delete
    const bulkDeleteBtn = document.getElementById('bulk-delete');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function () {
            const selectedIds = Array.from(document.querySelectorAll('.notification-checkbox:checked'))
                .map(cb => cb.value);

            if (selectedIds.length === 0) {
                showToast('Selectați cel puțin o notificare pentru ștergere.', 'warning');
                return;
            }

            if (confirm(`Sigur doriți să ștergeți ${selectedIds.length} notificări selectate?`)) {
                notificationManager.bulkDelete(selectedIds);
            }
        });
    }

    // Update bulk delete button state
    function updateBulkDeleteButton() {
        const selectedCount = document.querySelectorAll('.notification-checkbox:checked').length;
        const bulkDeleteBtn = document.getElementById('bulk-delete');

        if (bulkDeleteBtn) {
            bulkDeleteBtn.disabled = selectedCount === 0;
            bulkDeleteBtn.textContent = selectedCount > 0 ?
                `Șterge selectate (${selectedCount})` : 'Șterge selectate';
        }
    }

    // Listen for checkbox changes
    document.addEventListener('change', function (e) {
        if (e.target.classList.contains('notification-checkbox')) {
            updateBulkDeleteButton();
        }
    });

    // Toggle read status
    document.addEventListener('click', function (e) {
        if (e.target.closest('.toggle-read-btn')) {
            const btn = e.target.closest('.toggle-read-btn');
            const notificationId = btn.dataset.notificationId;
            const isRead = btn.dataset.isRead === 'true';

            notificationManager.toggleReadStatus(notificationId, !isRead);
        }
    });

    // Delete notification
    document.addEventListener('click', function (e) {
        if (e.target.closest('.delete-btn')) {
            const btn = e.target.closest('.delete-btn');
            const notificationId = btn.dataset.notificationId;

            if (confirm('Sigur doriți să ștergeți această notificare?')) {
                notificationManager.deleteNotification(notificationId);
            }
        }
    });

    // Auto-refresh unread count every 30 seconds
    setInterval(() => {
        notificationManager.updateUnreadCount();
    }, 30000);
});

function showToast(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    if (!toast) return;

    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header');

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
