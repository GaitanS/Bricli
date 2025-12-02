document.addEventListener('DOMContentLoaded', function () {
    // Scroll to bottom of messages
    const messagesContainer = document.querySelector('.messages-container');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Mark conversation as read
        const markReadUrl = messagesContainer.dataset.markReadUrl;
        const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');

        if (markReadUrl && csrfTokenInput) {
            fetch(markReadUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfTokenInput.value,
                    'Content-Type': 'application/json',
                },
            }).catch(error => {
                console.error('Error marking conversation as read:', error);
            });
        }
    }
});
