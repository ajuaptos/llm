document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('results');

    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const query = searchInput.value;

        if (query) {
            const results = await submitSearch(query);
            displayResults(results);
        }
    });

    function displayResults(results) {
        resultsContainer.innerHTML = '';

        if (results && results.length > 0) {
            results.forEach(result => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.textContent = result; // Adjust based on the structure of the result
                resultsContainer.appendChild(resultItem);
            });
        } else {
            resultsContainer.textContent = 'No results found.';
        }
    }
});