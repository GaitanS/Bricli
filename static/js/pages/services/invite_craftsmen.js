document.addEventListener('DOMContentLoaded', function () {
    const checkboxes = document.querySelectorAll('.craftsman-checkbox');
    const inviteBtn = document.getElementById('invite-btn');
    const selectedCount = document.getElementById('selected-count');
    const craftsmanCards = document.querySelectorAll('.craftsman-card');

    // Handle card clicks
    craftsmanCards.forEach(card => {
        card.addEventListener('click', function (e) {
            if (e.target.type !== 'checkbox') {
                const checkbox = this.querySelector('.craftsman-checkbox');
                checkbox.checked = !checkbox.checked;
                updateSelection();
            }
        });
    });

    // Handle checkbox changes
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelection);
    });

    function updateSelection() {
        const selected = document.querySelectorAll('.craftsman-checkbox:checked');
        const count = selected.length;

        selectedCount.textContent = count;
        inviteBtn.disabled = count === 0;

        // Update card styles
        craftsmanCards.forEach(card => {
            const checkbox = card.querySelector('.craftsman-checkbox');
            if (checkbox.checked) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });

        // Update button text
        if (count > 0) {
            inviteBtn.innerHTML = `<i class="fas fa-paper-plane me-2"></i>Invită ${count} Meșteri`;
        } else {
            inviteBtn.innerHTML = `<i class="fas fa-paper-plane me-2"></i>Trimite Invitații`;
        }
    }
});
