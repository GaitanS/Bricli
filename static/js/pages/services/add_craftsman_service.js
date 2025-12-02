document.addEventListener('DOMContentLoaded', function () {
    // We need to get the IDs from the template, but since this is an external file, we can't use Django template tags directly.
    // However, we can assume standard Django ID naming convention: id_field_name
    // Or we can look for elements by name or other attributes.
    // The template used: {{ form.service.id_for_label }} which usually resolves to id_service

    const serviceSelect = document.getElementById('id_service');
    const priceFromInput = document.getElementById('id_price_from');
    const priceToInput = document.getElementById('id_price_to');
    const priceUnitInput = document.getElementById('id_price_unit');

    const previewService = document.getElementById('preview-service');
    // const previewCategory = document.getElementById('preview-category'); // Not used in original script logic effectively
    const previewPrice = document.getElementById('preview-price');
    const previewUnit = document.getElementById('preview-unit');

    function updatePreview() {
        // Update service name
        if (serviceSelect && serviceSelect.selectedIndex > 0) {
            const selectedOption = serviceSelect.options[serviceSelect.selectedIndex];
            if (previewService) previewService.textContent = selectedOption.text;
        }

        // Update price
        const priceFrom = priceFromInput ? priceFromInput.value : '';
        const priceTo = priceToInput ? priceToInput.value : '';
        const unit = priceUnitInput ? priceUnitInput.value : '';

        let priceText = 'Preț la cerere';
        if (priceFrom && priceTo) {
            priceText = `${priceFrom} - ${priceTo} RON`;
        } else if (priceFrom) {
            priceText = `De la ${priceFrom} RON`;
        } else if (priceTo) {
            priceText = `Până la ${priceTo} RON`;
        }

        if (previewPrice) previewPrice.textContent = priceText;
        if (previewUnit) previewUnit.textContent = unit ? `/ ${unit}` : '';
    }

    // Add event listeners if elements exist
    if (serviceSelect) serviceSelect.addEventListener('change', updatePreview);
    if (priceFromInput) priceFromInput.addEventListener('input', updatePreview);
    if (priceToInput) priceToInput.addEventListener('input', updatePreview);
    if (priceUnitInput) priceUnitInput.addEventListener('input', updatePreview);
});
