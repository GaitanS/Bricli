/**
 * Search Filters - Mobile filter counter and category search
 */

(function () {
    'use strict';

    /**
     * Count active filters and update mobile button text
     */
    function countActiveFilters() {
        const params = new URLSearchParams(window.location.search);
        let count = 0;

        // Count non-empty filter parameters
        ['county', 'category', 'rating'].forEach(function (key) {
            const value = params.get(key);
            if (value && value !== '') {
                count++;
            }
        });

        // Update button text
        const filterBtn = document.getElementById('filterBtn');
        const filterBtnText = document.getElementById('filterBtnText');

        if (filterBtn && filterBtnText) {
            if (count > 0) {
                filterBtnText.textContent = 'Filtrează (' + count + ')';
            } else {
                filterBtnText.textContent = 'Filtrează';
            }
        }
    }

    /**
     * Filter category options in offcanvas based on search input
     * @param {string} term - Search term
     */
    window.filterCatOptions = function (term) {
        term = (term || '').toLowerCase();
        const container = document.getElementById('categoryScroll');
        if (!container) return;

        const categoryOptions = container.querySelectorAll('.category-option');
        const noMatchMsg = document.getElementById('noCatMatch');

        let hasMatch = false;

        // Show/hide categories based on match
        categoryOptions.forEach(function (div) {
            const label = div.querySelector('label');
            if (!label) return;

            const text = label.textContent.toLowerCase();
            const matches = text.includes(term);

            div.style.display = matches ? '' : 'none';
            if (matches) hasMatch = true;
        });

        // Show/hide "no match" message
        if (noMatchMsg) {
            noMatchMsg.style.display = hasMatch ? 'none' : '';
        }
    };

    /**
     * Initialize on page load
     */
    document.addEventListener('DOMContentLoaded', function () {
        countActiveFilters();

        // Update counter when offcanvas closes (in case filters changed)
        const offcanvas = document.getElementById('filtersOffcanvas');
        if (offcanvas) {
            offcanvas.addEventListener('hidden.bs.offcanvas', function () {
                // Counter will be updated on page reload after form submit
                // This is just a visual update if user cancels
            });
        }
    });
})();
