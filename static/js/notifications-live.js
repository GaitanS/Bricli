/**
 * Live Notifications System
 * Polls the server for unread notification count and updates badges in real-time
 */

(function() {
    'use strict';

    // Configuration
    const POLL_INTERVAL = 30000; // 30 seconds
    const API_ENDPOINT = '/notifications/api/notifications/unread-count/';

    // Badge elements
    const notificationsBadge = document.getElementById('notifications-badge');
    const notificationsBadgeMobile = document.getElementById('notifications-badge-mobile');
    const navbarNotificationBadge = document.getElementById('navbar-notification-badge');
    const navbarNotificationBadgeMobileTop = document.getElementById('navbar-notification-badge-mobile-top');

    let previousCount = 0;
    let pollTimer = null;

    /**
     * Fetch unread notifications count from API
     */
    async function fetchUnreadCount() {
        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.unread_count || 0;
        } catch (error) {
            console.error('Error fetching unread notifications count:', error);
            return null;
        }
    }

    /**
     * Update badge elements with new count
     */
    function updateBadges(count) {
        const countText = count > 99 ? '99+' : count.toString();

        // Update desktop dropdown badge
        if (notificationsBadge) {
            if (count > 0) {
                notificationsBadge.textContent = countText;
                notificationsBadge.style.display = '';
            } else {
                notificationsBadge.style.display = 'none';
            }
        }

        // Update mobile dropdown badge
        if (notificationsBadgeMobile) {
            if (count > 0) {
                // Extract the text node (first child) and update it
                const textNode = notificationsBadgeMobile.firstChild;
                if (textNode && textNode.nodeType === Node.TEXT_NODE) {
                    textNode.textContent = countText + ' ';
                } else {
                    notificationsBadgeMobile.insertBefore(
                        document.createTextNode(countText + ' '),
                        notificationsBadgeMobile.firstChild
                    );
                }
                notificationsBadgeMobile.style.display = '';
            } else {
                notificationsBadgeMobile.style.display = 'none';
            }
        }

        // Update navbar notification badge (desktop)
        if (navbarNotificationBadge) {
            if (count > 0) {
                navbarNotificationBadge.textContent = countText;
                navbarNotificationBadge.style.display = '';
            } else {
                navbarNotificationBadge.style.display = 'none';
            }
        }

        // Update navbar notification badge (mobile top)
        if (navbarNotificationBadgeMobileTop) {
            if (count > 0) {
                navbarNotificationBadgeMobileTop.textContent = countText;
                navbarNotificationBadgeMobileTop.style.display = '';
            } else {
                navbarNotificationBadgeMobileTop.style.display = 'none';
            }
        }
    }

    /**
     * Show notification animation/alert
     */
    function showNewNotificationAlert(count) {
        // Add subtle animation to dropdown badges
        if (notificationsBadge) {
            notificationsBadge.classList.add('animate-pulse');
            setTimeout(() => {
                notificationsBadge.classList.remove('animate-pulse');
            }, 1000);
        }

        if (notificationsBadgeMobile) {
            notificationsBadgeMobile.classList.add('animate-pulse');
            setTimeout(() => {
                notificationsBadgeMobile.classList.remove('animate-pulse');
            }, 1000);
        }

        // Add subtle animation to navbar badges
        if (navbarNotificationBadge) {
            navbarNotificationBadge.classList.add('animate-pulse');
            setTimeout(() => {
                navbarNotificationBadge.classList.remove('animate-pulse');
            }, 1000);
        }

        if (navbarNotificationBadgeMobileTop) {
            navbarNotificationBadgeMobileTop.classList.add('animate-pulse');
            setTimeout(() => {
                navbarNotificationBadgeMobileTop.classList.remove('animate-pulse');
            }, 1000);
        }

        // Optional: Play subtle notification sound
        // playNotificationSound();

        // Optional: Show browser notification (if permission granted)
        // showBrowserNotification(count);
    }

    /**
     * Main polling function
     */
    async function pollNotifications() {
        const count = await fetchUnreadCount();

        if (count !== null) {
            // Check if count has increased (new notification)
            if (count > previousCount && previousCount !== 0) {
                showNewNotificationAlert(count);
            }

            // Update badges
            updateBadges(count);

            // Store current count
            previousCount = count;
        }
    }

    /**
     * Initialize the notification system
     */
    function init() {
        // Get initial count from page load
        if (notificationsBadge && notificationsBadge.textContent) {
            const initialCount = parseInt(notificationsBadge.textContent);
            if (!isNaN(initialCount)) {
                previousCount = initialCount;
            }
        }

        // Start polling immediately
        pollNotifications();

        // Set up interval polling
        pollTimer = setInterval(pollNotifications, POLL_INTERVAL);

        // Add CSS for pulse animation
        addPulseAnimation();

        console.log('Live notifications system initialized (polling every 30s)');
    }

    /**
     * Add CSS for pulse animation
     */
    function addPulseAnimation() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse-badge {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.2);
                }
            }

            .animate-pulse {
                animation: pulse-badge 0.5s ease-in-out 2;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Clean up on page unload
     */
    function cleanup() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Clean up on page unload
    window.addEventListener('beforeunload', cleanup);

    // Expose API for debugging
    window.NotificationsLive = {
        poll: pollNotifications,
        getCount: () => previousCount
    };
})();
