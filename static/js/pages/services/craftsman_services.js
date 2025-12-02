document.addEventListener('DOMContentLoaded', function () {
    // Show All Services Logic (Mobile)
    const showAllBtn = document.getElementById('showAllMyServices');
    if (showAllBtn) {
        const servicesGrid = document.getElementById('myServicesGrid');
        const serviceItems = servicesGrid.querySelectorAll('.svc-item');
        const limit = 6;

        // Initially hide items beyond limit
        if (serviceItems.length > limit) {
            serviceItems.forEach((item, index) => {
                if (index >= limit) {
                    item.style.display = 'none';
                }
            });
        }

        showAllBtn.addEventListener('click', function () {
            // Show all items
            serviceItems.forEach(item => {
                item.style.display = 'block';
            });
            // Hide button
            this.style.display = 'none';
        });
    }

    // Confirmation Dialogs
    const confirmLinks = document.querySelectorAll('a[onclick^="return confirm"]');
    confirmLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            // Extract message from onclick attribute
            const onclickAttr = this.getAttribute('onclick');
            const match = onclickAttr.match(/confirm\('(.+)'\)/);
            const message = match ? match[1] : 'Ești sigur?';

            // Remove onclick attribute to prevent double execution if we were to keep it
            // But since we are replacing it, we prevent default and show confirm
            e.preventDefault();
            if (confirm(message)) {
                window.location.href = this.href;
            }
        });
        // Remove the inline onclick attribute to clean up
        link.removeAttribute('onclick');
    });

    const confirmForms = document.querySelectorAll('form[onsubmit^="return confirm"]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const onsubmitAttr = this.getAttribute('onsubmit');
            const match = onsubmitAttr.match(/confirm\('(.+)'\)/);
            const message = match ? match[1] : 'Ești sigur?';

            if (!confirm(message)) {
                e.preventDefault();
            }
        });
        form.removeAttribute('onsubmit');
    });

    // FAB Button
    const fabBtn = document.querySelector('.fab-add');
    if (fabBtn) {
        fabBtn.addEventListener('click', function () {
            // The onclick was window.location.href='...'
            // We can just use the data-url or similar if we updated the HTML
            // But since we are extracting, let's assume we update the HTML to use data-url or just href on an anchor
            // For now, let's check if it has an onclick we need to handle or if we replaced it
            // The original was: onclick="window.location.href='{% url 'services:add_craftsman_service' %}'"
            // We should probably change the button to an <a> tag in the HTML or add data-url
        });
    }
});
