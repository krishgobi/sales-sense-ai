document.addEventListener('DOMContentLoaded', function() {
    // Initialize category filter
    const categoryFilter = document.getElementById('categoryFilter');
    const searchInput = document.getElementById('searchInput');
    const productsGrid = document.getElementById('productsGrid');

    if (productsGrid) {
        // Get all unique categories
        const categories = new Set();
        document.querySelectorAll('.product-card').forEach(card => {
            categories.add(card.dataset.category);
        });

        // Populate category filter
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });

        // Filter function
        function filterProducts() {
            const selectedCategory = categoryFilter.value.toLowerCase();
            const searchTerm = searchInput.value.toLowerCase();

            document.querySelectorAll('.product-card').forEach(card => {
                const category = card.dataset.category.toLowerCase();
                const name = card.dataset.name.toLowerCase();
                const matchesCategory = !selectedCategory || category === selectedCategory;
                const matchesSearch = !searchTerm || name.includes(searchTerm);
                
                card.style.display = matchesCategory && matchesSearch ? '' : 'none';
            });
        }

        // Add event listeners
        categoryFilter.addEventListener('change', filterProducts);
        searchInput.addEventListener('input', filterProducts);
    }
});