// Notifications JavaScript

class NotificationManager {
    constructor() {
        this.baseUrl = '/notifications/';
        this.apiUrl = '/notifications/api/';
        this.csrfToken = this.getCSRFToken();
        this.unreadCount = 0;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.updateUnreadCount();
        this.initializeServiceWorker();
        this.setupEventListeners();
        this.isInitialized = true;
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Update unread notification count
    async updateUnreadCount() {
        try {
            const response = await fetch(`${this.apiUrl}stats/`, {
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.unreadCount = data.unread;
                this.updateUnreadBadge(data.unread);
            }
        } catch (error) {
            console.error('Error updating unread count:', error);
        }
    }
    
    // Update unread badge in navigation
    updateUnreadBadge(count) {
        const badges = document.querySelectorAll('.notification-counter, .unread-count');
        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });
    }
    
    // Toggle read status of a notification
    async toggleReadStatus(notificationId, isRead) {
        try {
            const response = await fetch(`${this.baseUrl}ajax/toggle-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ is_read: isRead })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update UI
                const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    if (isRead) {
                        notificationItem.classList.remove('unread');
                    } else {
                        notificationItem.classList.add('unread');
                    }
                }
                
                // Update unread count
                this.updateUnreadCount();
                
                return data;
            } else {
                throw new Error('Failed to toggle read status');
            }
        } catch (error) {
            console.error('Error toggling read status:', error);
            this.showToast('Eroare la actualizarea statusului notificării.', 'error');
            throw error;
        }
    }
    
    // Delete a notification
    async deleteNotification(notificationId) {
        try {
            const response = await fetch(`${this.baseUrl}ajax/delete/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            if (response.ok) {
                // Remove from UI
                const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.style.transition = 'all 0.3s ease';
                    notificationItem.style.opacity = '0';
                    notificationItem.style.transform = 'translateX(-100%)';
                    
                    setTimeout(() => {
                        notificationItem.remove();
                    }, 300);
                }
                
                // Update unread count
                this.updateUnreadCount();
                
                return true;
            } else {
                throw new Error('Failed to delete notification');
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
            this.showToast('Eroare la ștergerea notificării.', 'error');
            throw error;
        }
    }
    
    // Mark all notifications as read
    async markAllAsRead() {
        try {
            const response = await fetch(`${this.apiUrl}bulk-read/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ action: 'mark_read' })
            });
            
            if (response.ok) {
                // Update UI
                const unreadItems = document.querySelectorAll('.notification-item.unread');
                unreadItems.forEach(item => {
                    item.classList.remove('unread');
                });
                
                // Update unread count
                this.updateUnreadCount();
                
                this.showToast('Toate notificările au fost marcate ca citite.', 'success');
                return true;
            } else {
                throw new Error('Failed to mark all as read');
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
            this.showToast('Eroare la marcarea notificărilor ca citite.', 'error');
            throw error;
        }
    }
    
    // Bulk delete notifications
    async bulkDelete(notificationIds) {
        try {
            const response = await fetch(`${this.apiUrl}bulk-delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ notification_ids: notificationIds })
            });
            
            if (response.ok) {
                // Remove from UI
                notificationIds.forEach(id => {
                    const item = document.querySelector(`[data-notification-id="${id}"]`);
                    if (item) {
                        item.style.transition = 'all 0.3s ease';
                        item.style.opacity = '0';
                        item.style.transform = 'translateX(-100%)';
                        
                        setTimeout(() => {
                            item.remove();
                        }, 300);
                    }
                });
                
                // Update unread count
                this.updateUnreadCount();
                
                this.showToast(`${notificationIds.length} notificări au fost șterse.`, 'success');
                return true;
            } else {
                throw new Error('Failed to bulk delete');
            }
        } catch (error) {
            console.error('Error bulk deleting:', error);
            this.showToast('Eroare la ștergerea notificărilor.', 'error');
            throw error;
        }
    }
    
    // Initialize service worker for push notifications
    async initializeServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('Service Worker registered:', registration);
                
                // Listen for messages from service worker
                navigator.serviceWorker.addEventListener('message', event => {
                    if (event.data && event.data.type === 'NOTIFICATION_CLICKED') {
                        this.handleNotificationClick(event.data.notificationId);
                    }
                });
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    // Handle notification click from service worker
    handleNotificationClick(notificationId) {
        // Mark as read and navigate to notification
        this.toggleReadStatus(notificationId, true).then(() => {
            window.location.href = `${this.baseUrl}${notificationId}/`;
        });
    }
    
    // Setup event listeners
    setupEventListeners() {
        // Listen for real-time notifications via WebSocket or Server-Sent Events
        this.setupRealTimeUpdates();
        
        // Listen for visibility change to update unread count
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.updateUnreadCount();
            }
        });
    }
    
    // Setup real-time updates (WebSocket or SSE)
    setupRealTimeUpdates() {
        // Check if WebSocket is available
        if (typeof WebSocket !== 'undefined') {
            this.setupWebSocket();
        } else {
            // Fallback to polling
            this.setupPolling();
        }
    }
    
    // Setup WebSocket connection for real-time updates
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected for notifications');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealTimeNotification(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected, attempting to reconnect...');
                // Reconnect after 5 seconds
                setTimeout(() => {
                    this.setupWebSocket();
                }, 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                // Fallback to polling
                this.setupPolling();
            };
        } catch (error) {
            console.error('WebSocket setup failed:', error);
            this.setupPolling();
        }
    }
    
    // Setup polling as fallback
    setupPolling() {
        setInterval(() => {
            this.updateUnreadCount();
        }, 30000); // Poll every 30 seconds
    }
    
    // Handle real-time notification
    handleRealTimeNotification(data) {
        if (data.type === 'new_notification') {
            this.showNewNotification(data.notification);
            this.updateUnreadCount();
        } else if (data.type === 'notification_read') {
            this.updateNotificationStatus(data.notification_id, true);
        } else if (data.type === 'notification_deleted') {
            this.removeNotificationFromUI(data.notification_id);
        }
    }
    
    // Show new notification
    showNewNotification(notification) {
        // Show browser notification if permission granted
        if (Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/logo-small.png',
                tag: `notification-${notification.id}`,
                data: { notificationId: notification.id }
            });
        }
        
        // Show toast notification
        this.showToast(`Notificare nouă: ${notification.title}`, 'info');
        
        // Add to notification list if on notifications page
        if (window.location.pathname.includes('/notifications/')) {
            this.addNotificationToList(notification);
        }
    }
    
    // Add notification to list
    addNotificationToList(notification) {
        const notificationList = document.querySelector('.list-group');
        if (!notificationList) return;
        
        const notificationHtml = this.createNotificationHTML(notification);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = notificationHtml;
        const notificationElement = tempDiv.firstElementChild;
        
        // Add animation class
        notificationElement.classList.add('notification-new');
        
        // Insert at the beginning of the list
        notificationList.insertBefore(notificationElement, notificationList.firstChild);
        
        // Remove animation class after animation completes
        setTimeout(() => {
            notificationElement.classList.remove('notification-new');
        }, 500);
    }
    
    // Create notification HTML
    createNotificationHTML(notification) {
        const timeAgo = this.timeAgo(new Date(notification.created_at));
        const priorityClass = notification.priority || 'secondary';
        
        return `
            <div class="list-group-item notification-item unread" data-notification-id="${notification.id}">
                <div class="d-flex align-items-start">
                    <div class="form-check me-3">
                        <input class="form-check-input notification-checkbox" type="checkbox" value="${notification.id}">
                    </div>
                    
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="mb-1 notification-title">
                                <i class="fas fa-circle text-primary me-1" style="font-size: 0.5rem;"></i>
                                ${notification.title}
                            </h6>
                            <div class="d-flex align-items-center">
                                <span class="badge bg-${priorityClass} me-2">
                                    ${notification.priority_display || 'Normal'}
                                </span>
                                <small class="text-muted">${timeAgo}</small>
                            </div>
                        </div>
                        
                        <p class="mb-2 text-muted notification-message">
                            ${this.truncateText(notification.message, 20)}
                        </p>
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge bg-light text-dark">
                                    ${notification.type_display || notification.notification_type}
                                </span>
                            </div>
                            
                            <div class="btn-group" role="group">
                                <a href="/notifications/${notification.id}/" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-eye"></i>
                                </a>
                                <button type="button" class="btn btn-outline-secondary btn-sm toggle-read-btn"
                                        data-notification-id="${notification.id}" data-is-read="false">
                                    <i class="fas fa-envelope-open"></i>
                                </button>
                                <button type="button" class="btn btn-outline-danger btn-sm delete-btn"
                                        data-notification-id="${notification.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Update notification status in UI
    updateNotificationStatus(notificationId, isRead) {
        const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationItem) {
            if (isRead) {
                notificationItem.classList.remove('unread');
            } else {
                notificationItem.classList.add('unread');
            }
        }
    }
    
    // Remove notification from UI
    removeNotificationFromUI(notificationId) {
        const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationItem) {
            notificationItem.style.transition = 'all 0.3s ease';
            notificationItem.style.opacity = '0';
            notificationItem.style.transform = 'translateX(-100%)';
            
            setTimeout(() => {
                notificationItem.remove();
            }, 300);
        }
    }
    
    // Show toast notification
    showToast(message, type = 'info', duration = 5000) {
        // Create toast element if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast bg-${type === 'error' ? 'danger' : type} text-white" role="alert">
                <div class="toast-header bg-transparent text-white border-0">
                    <i class="fas fa-bell me-2"></i>
                    <strong class="me-auto">Notificare</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    
    // Utility functions
    timeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'acum câteva secunde';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} ${minutes === 1 ? 'minut' : 'minute'} în urmă`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} ${hours === 1 ? 'oră' : 'ore'} în urmă`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} ${days === 1 ? 'zi' : 'zile'} în urmă`;
        }
    }
    
    truncateText(text, wordLimit) {
        const words = text.split(' ');
        if (words.length <= wordLimit) {
            return text;
        }
        return words.slice(0, wordLimit).join(' ') + '...';
    }
}

// Push notification utilities
class PushNotificationManager {
    constructor() {
        this.vapidPublicKey = null;
        this.subscription = null;
    }
    
    async initialize() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push notifications not supported');
            return false;
        }
        
        try {
            const registration = await navigator.serviceWorker.ready;
            this.subscription = await registration.pushManager.getSubscription();
            return true;
        } catch (error) {
            console.error('Error initializing push notifications:', error);
            return false;
        }
    }
    
    async requestPermission() {
        if (Notification.permission === 'granted') {
            return true;
        }
        
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
    
    async subscribe() {
        if (!await this.requestPermission()) {
            throw new Error('Permission denied');
        }
        
        const registration = await navigator.serviceWorker.ready;
        
        // Get VAPID public key
        const response = await fetch('/notifications/api/push/vapid-key/');
        const data = await response.json();
        this.vapidPublicKey = data.public_key;
        
        // Subscribe to push notifications
        this.subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
        });
        
        // Send subscription to server
        await this.sendSubscriptionToServer();
        
        return this.subscription;
    }
    
    async unsubscribe() {
        if (this.subscription) {
            await this.subscription.unsubscribe();
            this.subscription = null;
            
            // Remove subscription from server
            await fetch('/notifications/api/push/unsubscribe/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
        }
    }
    
    async sendSubscriptionToServer() {
        await fetch('/notifications/api/push/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                subscription: this.subscription.toJSON()
            })
        });
    }
    
    urlBase64ToUint8Array(base64String) {
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
}

// Initialize notification manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.notificationManager = new NotificationManager();
    window.pushNotificationManager = new PushNotificationManager();
    
    // Initialize push notifications
    window.pushNotificationManager.initialize();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NotificationManager, PushNotificationManager };
}