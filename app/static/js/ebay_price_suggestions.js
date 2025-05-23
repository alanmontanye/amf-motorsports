/**
 * eBay Price Suggestion Integration
 * 
 * This script adds price analysis functionality to part creation and editing forms.
 * It fetches price suggestions from eBay when the user enters part information.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const partForm = document.getElementById('part-form');
    const atvSelect = document.getElementById('atv_id');
    const partNameInput = document.getElementById('name');
    const listPriceInput = document.getElementById('list_price');
    const priceContainer = document.getElementById('price-suggestion-container');
    
    // Hidden part_id field for edit mode
    const partIdInput = document.getElementById('part_id');
    
    // Check if we're on a part form page
    if (!partForm || !atvSelect || !partNameInput || !listPriceInput) {
        return;
    }
    
    // Add the price suggestion container if it doesn't exist
    if (!priceContainer) {
        const container = document.createElement('div');
        container.id = 'price-suggestion-container';
        container.className = 'mt-2 mb-3 d-none';
        
        const card = document.createElement('div');
        card.className = 'card border-info';
        
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header bg-info text-white d-flex justify-content-between align-items-center';
        cardHeader.innerHTML = '<h6 class="mb-0"><i class="fas fa-tags mr-2"></i> eBay Price Analysis</h6>';
        
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'close text-white';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', function() {
            container.classList.add('d-none');
        });
        
        cardHeader.appendChild(closeBtn);
        card.appendChild(cardHeader);
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        cardBody.innerHTML = `
            <div id="price-loading" class="text-center">
                <div class="spinner-border text-info" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <p>Analyzing eBay prices...</p>
            </div>
            <div id="price-results" class="d-none">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Sold Items</h6>
                        <p id="sold-stats">No data available</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Active Listings</h6>
                        <p id="active-stats">No data available</p>
                    </div>
                </div>
                <div class="alert alert-info mt-2">
                    <strong>Suggested Price: $<span id="suggested-price">0.00</span></strong>
                    <button id="apply-price" class="btn btn-sm btn-primary ml-3">Apply This Price</button>
                </div>
            </div>
            <div id="price-error" class="d-none">
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    <span id="error-message"></span>
                </div>
            </div>
        `;
        
        card.appendChild(cardBody);
        container.appendChild(card);
        
        // Insert after the list price field
        listPriceInput.parentNode.parentNode.after(container);
    }
    
    // Update the container reference (whether it existed or we created it)
    const applyPriceBtn = document.getElementById('apply-price');
    
    if (applyPriceBtn) {
        applyPriceBtn.addEventListener('click', function() {
            const suggestedPrice = document.getElementById('suggested-price').textContent;
            listPriceInput.value = suggestedPrice;
        });
    }
    
    // Add a "Get Price Suggestion" button next to the price field
    const priceGroup = listPriceInput.parentNode;
    const suggestBtn = document.createElement('button');
    suggestBtn.type = 'button';
    suggestBtn.className = 'btn btn-info ml-2';
    suggestBtn.innerHTML = '<i class="fas fa-magic mr-1"></i> Suggest Price';
    suggestBtn.id = 'suggest-price-btn';
    
    // If the price field is wrapped in an input group, add it to the append
    const inputGroup = priceGroup.querySelector('.input-group');
    if (inputGroup) {
        const inputGroupAppend = document.createElement('div');
        inputGroupAppend.className = 'input-group-append';
        inputGroupAppend.appendChild(suggestBtn);
        inputGroup.appendChild(inputGroupAppend);
    } else {
        // Otherwise, wrap the field and button in a new div
        const wrapper = document.createElement('div');
        wrapper.className = 'd-flex align-items-center';
        listPriceInput.parentNode.insertBefore(wrapper, listPriceInput);
        wrapper.appendChild(listPriceInput);
        wrapper.appendChild(suggestBtn);
    }
    
    // Add a debounce function for input handling
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
    
    // Function to fetch price suggestions
    function fetchPriceSuggestion() {
        const atvId = atvSelect.value;
        const partName = partNameInput.value;
        const partId = partIdInput ? partIdInput.value : null;
        
        // Need minimum data to proceed
        if ((!atvId || !partName) && !partId) {
            return;
        }
        
        // Show the container and loading state
        priceContainer.classList.remove('d-none');
        document.getElementById('price-loading').classList.remove('d-none');
        document.getElementById('price-results').classList.add('d-none');
        document.getElementById('price-error').classList.add('d-none');
        
        // Build query parameters
        let params = new URLSearchParams();
        if (partId) {
            params.append('part_id', partId);
        } else {
            params.append('atv_id', atvId);
            params.append('part_name', partName);
        }
        
        // Make the API request
        fetch(`/atv/ebay/api/price-suggestion?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('price-loading').classList.add('d-none');
                
                if (data.success) {
                    // Update the results
                    document.getElementById('price-results').classList.remove('d-none');
                    
                    // Format sold stats
                    if (data.sold_count) {
                        document.getElementById('sold-stats').innerHTML = `
                            Found ${data.sold_count} sold items<br>
                            Range: $${data.sold_min.toFixed(2)} - $${data.sold_max.toFixed(2)}<br>
                            Average: $${data.sold_avg.toFixed(2)}
                        `;
                    } else {
                        document.getElementById('sold-stats').textContent = 'No sold items found';
                    }
                    
                    // Format active stats
                    if (data.active_count) {
                        document.getElementById('active-stats').innerHTML = `
                            Found ${data.active_count} active listings<br>
                            Range: $${data.active_min.toFixed(2)} - $${data.active_max.toFixed(2)}<br>
                            Average: $${data.active_avg.toFixed(2)}
                        `;
                    } else {
                        document.getElementById('active-stats').textContent = 'No active listings found';
                    }
                    
                    // Update suggested price
                    document.getElementById('suggested-price').textContent = data.suggested_price.toFixed(2);
                } else {
                    // Show error
                    document.getElementById('price-error').classList.remove('d-none');
                    document.getElementById('error-message').textContent = data.message || 'Could not analyze prices';
                }
            })
            .catch(error => {
                document.getElementById('price-loading').classList.add('d-none');
                document.getElementById('price-error').classList.remove('d-none');
                document.getElementById('error-message').textContent = 'Network error. Please try again.';
                console.error('Error fetching price suggestions:', error);
            });
    }
    
    // Debounced version of the fetch function
    const debouncedFetch = debounce(fetchPriceSuggestion, 800);
    
    // Add event listeners
    suggestBtn.addEventListener('click', fetchPriceSuggestion);
    
    // Optional: Auto-suggest as user types (with debounce)
    const autoSuggestEnabled = false; // Set to true to enable auto-suggest
    if (autoSuggestEnabled) {
        partNameInput.addEventListener('input', debouncedFetch);
        atvSelect.addEventListener('change', debouncedFetch);
    }
});
