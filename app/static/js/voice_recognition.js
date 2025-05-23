/**
 * Voice Recognition for AMF Motorsports
 * 
 * This script adds voice input capabilities to forms, allowing users to dictate
 * part information instead of typing it.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if speech recognition is supported
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.log('Speech recognition not supported in this browser');
        return;
    }

    // Initialize speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    // Add dictate buttons to forms
    addDictateButtonToParts();
    addDictateButtonToATV();

    // Track the currently active form field
    let activeField = null;
    document.addEventListener('focus', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            activeField = e.target;
        }
    }, true);

    // Speech recognition result handler
    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript.trim();
        console.log('Recognized: ' + text);
        
        // Check if a specific field is active
        if (activeField) {
            activeField.value = text;
            activeField = null;
            return;
        }
        
        // Process comma-separated voice commands
        const parts = text.split(',');
        
        // Find the form we're working with
        const partForm = document.getElementById('part-form');
        const atvForm = document.getElementById('atv-form');
        
        if (partForm) {
            // Process part form fields
            processParts(parts, partForm);
        } else if (atvForm) {
            // Process ATV form fields
            processATV(parts, atvForm);
        }
    };

    // Error handler
    recognition.onerror = function(event) {
        console.error('Speech recognition error', event.error);
        const statusElement = document.getElementById('voice-status');
        if (statusElement) {
            statusElement.textContent = 'Error: ' + event.error;
            statusElement.className = 'text-danger';
        }
    };

    // Process completed handler
    recognition.onend = function() {
        const dictateBtn = document.getElementById('dictate-btn');
        if (dictateBtn) {
            dictateBtn.innerHTML = '<i class="fas fa-microphone"></i> Dictate';
            dictateBtn.classList.remove('btn-danger');
            dictateBtn.classList.add('btn-primary');
        }
        
        const statusElement = document.getElementById('voice-status');
        if (statusElement) {
            statusElement.textContent = 'Ready';
            statusElement.className = 'text-muted';
        }
    };

    // Process parts form voice input
    function processParts(parts, form) {
        parts.forEach(part => {
            const trimmed = part.trim().toLowerCase();
            
            // Name field
            if (trimmed.startsWith('name')) {
                const value = trimmed.replace(/^name\s+/i, '');
                const nameField = form.querySelector('[name="name"]');
                if (nameField) nameField.value = value;
            }
            
            // Part number
            else if (trimmed.startsWith('number')) {
                const value = trimmed.replace(/^number\s+/i, '');
                const numberField = form.querySelector('[name="part_number"]');
                if (numberField) numberField.value = value;
            }
            
            // Description
            else if (trimmed.startsWith('description')) {
                const value = trimmed.replace(/^description\s+/i, '');
                const descField = form.querySelector('[name="description"]');
                if (descField) descField.value = value;
            }
            
            // Price
            else if (trimmed.startsWith('price')) {
                let value = trimmed.replace(/^price\s+/i, '');
                // Remove dollar sign if present
                value = value.replace('$', '');
                const priceField = form.querySelector('[name="list_price"]');
                if (priceField) priceField.value = value;
            }
            
            // Cost
            else if (trimmed.startsWith('cost')) {
                let value = trimmed.replace(/^cost\s+/i, '');
                // Remove dollar sign if present
                value = value.replace('$', '');
                const costField = form.querySelector('[name="cost"]');
                if (costField) costField.value = value;
            }
            
            // Condition
            else if (trimmed.startsWith('condition')) {
                let value = trimmed.replace(/^condition\s+/i, '');
                
                // Map spoken condition to form values
                if (value.includes('new')) {
                    value = 'new';
                } else if (value.includes('good')) {
                    value = 'used_good';
                } else if (value.includes('fair')) {
                    value = 'used_fair';
                } else if (value.includes('poor')) {
                    value = 'used_poor';
                }
                
                const conditionField = form.querySelector('[name="condition"]');
                if (conditionField) conditionField.value = value;
            }
            
            // Storage/Tote
            else if (trimmed.startsWith('tote') || trimmed.startsWith('storage')) {
                let value = trimmed.replace(/^(tote|storage)\s+/i, '');
                
                // Try to find storage by name or ID
                const storageField = form.querySelector('[name="storage_id"]');
                if (storageField) {
                    // Find the option with matching text
                    const options = Array.from(storageField.options);
                    const match = options.find(option => 
                        option.text.toLowerCase().includes(value.toLowerCase()) || 
                        option.value === value
                    );
                    
                    if (match) {
                        storageField.value = match.value;
                    }
                }
            }
        });
    }

    // Process ATV form voice input
    function processATV(parts, form) {
        parts.forEach(part => {
            const trimmed = part.trim().toLowerCase();
            
            // Year
            if (trimmed.startsWith('year')) {
                const value = trimmed.replace(/^year\s+/i, '');
                const yearField = form.querySelector('[name="year"]');
                if (yearField) yearField.value = value;
            }
            
            // Make
            else if (trimmed.startsWith('make')) {
                const value = trimmed.replace(/^make\s+/i, '');
                const makeField = form.querySelector('[name="make"]');
                if (makeField) makeField.value = value;
            }
            
            // Model
            else if (trimmed.startsWith('model')) {
                const value = trimmed.replace(/^model\s+/i, '');
                const modelField = form.querySelector('[name="model"]');
                if (modelField) modelField.value = value;
            }
            
            // VIN
            else if (trimmed.startsWith('vin')) {
                const value = trimmed.replace(/^vin\s+/i, '');
                const vinField = form.querySelector('[name="vin"]');
                if (vinField) vinField.value = value;
            }
            
            // Purchase price
            else if (trimmed.startsWith('purchase') || trimmed.startsWith('price')) {
                let value = trimmed.replace(/^(purchase|price)\s+/i, '');
                // Remove dollar sign if present
                value = value.replace('$', '');
                const priceField = form.querySelector('[name="purchase_price"]');
                if (priceField) priceField.value = value;
            }
            
            // Purchase date
            else if (trimmed.startsWith('date')) {
                let value = trimmed.replace(/^date\s+/i, '');
                const dateField = form.querySelector('[name="purchase_date"]');
                if (dateField) dateField.value = value;
            }
            
            // Color
            else if (trimmed.startsWith('color')) {
                const value = trimmed.replace(/^color\s+/i, '');
                const colorField = form.querySelector('[name="color"]');
                if (colorField) colorField.value = value;
            }
        });
    }

    // Add dictate button to parts form
    function addDictateButtonToParts() {
        const partForm = document.getElementById('part-form');
        if (!partForm) return;
        
        const formTitle = partForm.querySelector('.card-header h5');
        if (formTitle) {
            addDictateButton(formTitle);
        }
        
        // Add a helper text area
        const helpText = document.createElement('div');
        helpText.className = 'alert alert-info mt-3';
        helpText.innerHTML = `
            <h6><i class="fas fa-info-circle"></i> Voice Input Examples:</h6>
            <ul>
                <li>"Name front fender bracket, number 12345, condition new, tote 2"</li>
                <li>"Name engine bolt, price 12.99, cost 5, condition used good"</li>
                <li>You can also click on any field and then the microphone to dictate just that field</li>
            </ul>
        `;
        
        // Insert after the first row
        const firstRow = partForm.querySelector('.row');
        if (firstRow) {
            firstRow.after(helpText);
        } else {
            partForm.insertBefore(helpText, partForm.firstChild);
        }
    }

    // Add dictate button to ATV form
    function addDictateButtonToATV() {
        const atvForm = document.getElementById('atv-form');
        if (!atvForm) return;
        
        const formTitle = atvForm.querySelector('.card-header h5');
        if (formTitle) {
            addDictateButton(formTitle);
        }
        
        // Add a helper text area
        const helpText = document.createElement('div');
        helpText.className = 'alert alert-info mt-3';
        helpText.innerHTML = `
            <h6><i class="fas fa-info-circle"></i> Voice Input Examples:</h6>
            <ul>
                <li>"Year 2010, make Honda, model TRX 400"</li>
                <li>"VIN 1HD1KBP13DB611440, price 1500, date 2023-05-22"</li>
                <li>You can also click on any field and then the microphone to dictate just that field</li>
            </ul>
        `;
        
        // Insert after the first row
        const firstRow = atvForm.querySelector('.row');
        if (firstRow) {
            firstRow.after(helpText);
        } else {
            atvForm.insertBefore(helpText, atvForm.firstChild);
        }
    }

    // Helper function to add dictate button
    function addDictateButton(element) {
        // Create button container
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'd-flex align-items-center';
        
        // Get the parent element
        const parent = element.parentNode;
        
        // Create dictate button
        const dictateBtn = document.createElement('button');
        dictateBtn.type = 'button';
        dictateBtn.id = 'dictate-btn';
        dictateBtn.className = 'btn btn-primary ml-3';
        dictateBtn.innerHTML = '<i class="fas fa-microphone"></i> Dictate';
        
        // Create status indicator
        const statusIndicator = document.createElement('span');
        statusIndicator.id = 'voice-status';
        statusIndicator.className = 'text-muted ml-2';
        statusIndicator.textContent = 'Ready';
        
        // Add click event
        dictateBtn.addEventListener('click', function() {
            // Toggle recording state
            if (recognition.recognizing) {
                recognition.stop();
                return;
            }
            
            // Start recording
            recognition.recognizing = true;
            this.innerHTML = '<i class="fas fa-stop"></i> Stop';
            this.classList.remove('btn-primary');
            this.classList.add('btn-danger');
            
            // Update status
            statusIndicator.textContent = 'Listening...';
            statusIndicator.className = 'text-success ml-2';
            
            // Start recognition
            try {
                recognition.start();
            } catch (e) {
                console.error('Recognition error', e);
            }
        });
        
        // Add button and status to container
        buttonContainer.appendChild(element.cloneNode(true));
        buttonContainer.appendChild(dictateBtn);
        buttonContainer.appendChild(statusIndicator);
        
        // Replace original element with container
        parent.replaceChild(buttonContainer, element);
    }
});
