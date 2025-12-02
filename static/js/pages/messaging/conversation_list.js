document.addEventListener('DOMContentLoaded', function () {
    // Click on conversation item to navigate
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function (e) {
            if (!e.target.closest('.btn')) {
                const conversationLink = this.querySelector('a[href*="conversation_detail"]');
                if (conversationLink) {
                    window.location.href = conversationLink.href;
                }
            }
        });
    });
});
