document.addEventListener('DOMContentLoaded', function () {
    // Initialize notification manager
    const notificationManager = new NotificationManager();
    const preferencesForm = document.getElementById('preferences-form');

    // Toggle quiet hours settings visibility
    const quietHoursEnabled = document.getElementById('quiet_hours_enabled');
    const quietHoursSettings = document.getElementById('quiet-hours-settings');

    function toggleQuietHoursSettings() {
        if (quietHoursEnabled.checked) {
            quietHoursSettings.style.display = 'block';
        } else {
            quietHoursSettings.style.display = 'none';
        }
    }

    if (quietHoursEnabled) {
        quietHoursEnabled.addEventListener('change', toggleQuietHoursSettings);
        toggleQuietHoursSettings(); // Initial state
    }

    // Check push notification support and subscription status
    checkPushSupport();

    // Enable push notifications
    const enablePushBtn = document.getElementById('enable-push-btn');
    if (enablePushBtn) {
        enablePushBtn.addEventListener('click', function () {
            enablePushNotifications();
        });
    }

    // Test push notification
    const testPushBtn = document.getElementById('test-push-btn');
    if (testPushBtn) {
        testPushBtn.addEventListener('click', function () {
            testPushNotification();
        });
    }

    // Form submission
    if (preferencesForm) {
        preferencesForm.addEventListener('submit', function (e) {
            e.preventDefault();
            savePreferences();
        });
    }

    function checkPushSupport() {
        const statusDiv = document.getElementById('push-subscription-status');
        const statusText = document.getElementById('subscription-text');
        const enableBtn = document.getElementById('enable-push-btn');

        if (!statusDiv) return;

        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            statusDiv.className = 'alert alert-warning';
            statusText.textContent = 'Browserul dvs. nu suportă notificările push.';
            return;
        }

        // Check if already subscribed
        navigator.serviceWorker.ready.then(registration => {
            return registration.pushManager.getSubscription();
        }).then(subscription => {
            if (subscription) {
                statusDiv.className = 'alert alert-success';
                statusText.textContent = 'Notificările push sunt activate.';
            } else {
                statusDiv.className = 'alert alert-info';
                statusText.textContent = 'Notificările push nu sunt activate.';
                if (enableBtn) enableBtn.classList.remove('d-none');
            }
        }).catch(error => {
            console.error('Error checking push subscription:', error);
            statusDiv.className = 'alert alert-danger';
            statusText.textContent = 'Eroare la verificarea statusului notificărilor push.';
        });
    }

    function enablePushNotifications() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            showToast('Browserul dvs. nu suportă notificările push.', 'error');
            return;
        }

        const vapidKeyUrl = preferencesForm.dataset.vapidKeyUrl;
        const subscribeUrl = preferencesForm.dataset.subscribeUrl;

        if (!vapidKeyUrl || !subscribeUrl) {
            console.error('Missing API URLs');
            return;
        }

        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                return navigator.serviceWorker.ready;
            } else {
                throw new Error('Permission denied');
            }
        }).then(registration => {
            // Get VAPID public key from server
            return fetch(vapidKeyUrl)
                .then(response => response.json())
                .then(data => {
                    return registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: urlBase64ToUint8Array(data.public_key)
                    });
                });
        }).then(subscription => {
            // Send subscription to server
            return fetch(subscribeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });
        }).then(response => {
            if (response.ok) {
                showToast('Notificările push au fost activate cu succes!', 'success');
                checkPushSupport(); // Refresh status
            } else {
                throw new Error('Failed to save subscription');
            }
        }).catch(error => {
            console.error('Error enabling push notifications:', error);
            showToast('Eroare la activarea notificărilor push.', 'error');
        });
    }

    function testPushNotification() {
        const testPushUrl = preferencesForm.dataset.testPushUrl;
        if (!testPushUrl) return;

        fetch(testPushUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).then(response => {
            if (response.ok) {
                showToast('Notificarea de test a fost trimisă!', 'success');
            } else {
                throw new Error('Failed to send test notification');
            }
        }).catch(error => {
            console.error('Error sending test notification:', error);
            showToast('Eroare la trimiterea notificării de test.', 'error');
        });
    }

    function savePreferences() {
        const formData = new FormData(preferencesForm);

        fetch(preferencesForm.action, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                showToast('Preferințele au fost salvate cu succes!', 'success');
            } else {
                throw new Error('Failed to save preferences');
            }
        }).catch(error => {
            console.error('Error saving preferences:', error);
            showToast('Eroare la salvarea preferințelor.', 'error');
        });
    }

    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
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
