function submitSearch(query) {
    return fetch('http://localhost:4000/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => data)
    .catch(error => {
        console.error('Error:', error);
    });
}

export { submitSearch };