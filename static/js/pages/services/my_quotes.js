document.addEventListener('DOMContentLoaded', function () {
    // Handle tab switching
    const tabs = document.querySelectorAll('#quoteTabs button[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            // Optional: analytics tracking or URL updates
        });
    });
});
