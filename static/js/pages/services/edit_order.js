document.addEventListener('DOMContentLoaded', function () {
    // Handle urgency selection
    const urgencyOptions = document.querySelectorAll('.urgency-option');
    urgencyOptions.forEach(option => {
        option.addEventListener('click', function () {
            // Remove selected class from all options
            urgencyOptions.forEach(opt => opt.classList.remove('selected'));

            // Add selected class to clicked option
            this.classList.add('selected');

            // Check the radio button
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });

    // Auto-resize description textarea
    const descriptionTextarea = document.getElementById('id_description');
    if (descriptionTextarea) {
        descriptionTextarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Initial resize
        descriptionTextarea.style.height = 'auto';
        descriptionTextarea.style.height = (descriptionTextarea.scrollHeight) + 'px';
    }

    // Handle county/city dependency
    const countySelect = document.getElementById('id_county');
    const citySelect = document.getElementById('id_city');

    if (countySelect && citySelect) {
        countySelect.addEventListener('change', function () {
            const countyId = this.value;

            // Clear city options
            citySelect.innerHTML = '<option value="">Selectează orașul</option>';

            if (countyId) {
                // Fetch cities for selected county
                fetch(`/api/cities/${countyId}/`)
                    .then(response => response.json())
                    .then(cities => {
                        cities.forEach(city => {
                            const option = document.createElement('option');
                            option.value = city.id;
                            option.textContent = city.name;
                            citySelect.appendChild(option);
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching cities:', error);
                    });
            }
        });
    }

    // Format budget inputs
    const budgetInputs = document.querySelectorAll('#id_budget_min, #id_budget_max');
    budgetInputs.forEach(input => {
        input.addEventListener('input', function (e) {
            // Remove non-numeric characters except decimal point
            let value = e.target.value.replace(/[^\d.]/g, '');

            // Ensure only one decimal point
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }

            // Limit decimal places to 2
            if (parts[1] && parts[1].length > 2) {
                value = parts[0] + '.' + parts[1].substring(0, 2);
            }

            e.target.value = value;
        });
    });
});
