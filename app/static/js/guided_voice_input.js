/**
 * Guided Voice Input System for AMF Motorsports
 * 
 * This script provides a step-by-step voice guidance system for adding
 * parts to ATVs, prompting the user for each field and handling the 
 * entire workflow via voice commands.
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

    // Initialize speech synthesis
    const synth = window.speechSynthesis;
    
    // Track our current state
    let isInGuidedMode = false;
    let currentAtvId = null;
    let currentStep = null;
    let partFormData = {};
    let partsAdded = 0;
    
    // Define the workflow steps - dynamically find form fields
    function detectFormFields() {
        const formFields = [];
        const form = document.querySelector('form');
        
        if (!form) return [];
        
        // Map of field names to their prompts and settings
        const fieldMappings = {
            'name': { prompt: 'What is the part name?', optional: false },
            'part_number': { prompt: 'What is the part number? Say "skip" if unknown.', optional: true },
            'condition': { prompt: 'What is the condition? New, used good, used fair, or used poor?', optional: false },
            'description': { prompt: 'Provide a brief description of the part, or say "skip".', optional: true },
            'list_price': { prompt: 'What is the list price?', optional: false },
            'source_price': { prompt: 'What was the cost of this part? Say "zero" if unknown.', optional: false },
            'storage_id': { prompt: 'Which storage location or tote is this part in?', optional: false },
            'location': { prompt: 'What specific location within the storage area? Say "skip" if not applicable.', optional: true },
        };
        
        // Get all input fields, selects, and textareas in the form
        const inputs = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
        
        // For each input, if it's in our mappings, add it to our workflow
        inputs.forEach(input => {
            let fieldName = input.name;
            if (fieldMappings[fieldName]) {
                formFields.push({
                    id: fieldName,
                    prompt: fieldMappings[fieldName].prompt,
                    field: fieldName,
                    optional: fieldMappings[fieldName].optional,
                    element: input
                });
            }
        });
        
        // Always add confirmation step at the end
        formFields.push({
            id: 'confirm',
            prompt: 'Ready to save this part. Say "save" to continue or "edit" to make changes.',
            field: null
        });
        
        return formFields;
    }
    
    // Get workflow steps dynamically based on the form
    const workflowSteps = detectFormFields();
    
    // Add the guided voice mode button to appropriate pages
    addGuidedModeButton();
    
    // Speech recognition result handler
    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript.trim().toLowerCase();
        console.log('Recognized: ' + text);
        
        handleVoiceInput(text);
    };

    // Error handler
    recognition.onerror = function(event) {
        console.error('Speech recognition error', event.error);
        updateStatusMessage('Error: ' + event.error, 'error');
        
        // If in guided mode, try again after a pause
        if (isInGuidedMode) {
            setTimeout(() => {
                speak("Sorry, I didn't catch that. Let's try again.");
                promptForCurrentStep();
            }, 1500);
        }
    };

    // Process completed handler
    recognition.onend = function() {
        if (isInGuidedMode) {
            // In guided mode, we want to keep listening after a short pause
            setTimeout(() => {
                if (isInGuidedMode) {
                    recognition.start();
                }
            }, 1000);
        } else {
            // Update UI when not in guided mode
            const dictateBtn = document.getElementById('guided-voice-btn');
            if (dictateBtn) {
                dictateBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Guided Voice Mode';
                dictateBtn.classList.remove('btn-danger');
                dictateBtn.classList.add('btn-success');
            }
        }
    };
    
    // Handle voice input based on current state
    function handleVoiceInput(text) {
        if (!isInGuidedMode) {
            // Not in guided mode, check for activation command
            if (text.includes('start guided') || text.includes('guided mode')) {
                startGuidedMode();
            }
            return;
        }
        
        // Exit command - works at any time
        if (text.includes('exit') || text.includes('quit') || text.includes('stop guided')) {
            exitGuidedMode();
            return;
        }
        
        // Switch ATV command
        if (text.includes('switch atv') || text.includes('change atv')) {
            speak("Please select a different ATV from the list and then restart guided mode.");
            exitGuidedMode();
            return;
        }
        
        // Handle special case for the confirm step
        if (currentStep === 'confirm') {
            if (text.includes('save') || text.includes('yes') || text.includes('confirm')) {
                savePart();
            } else if (text.includes('edit') || text.includes('change') || text.includes('modify')) {
                // Go back to first step to edit
                currentStep = workflowSteps[0].id;
                speak("Let's edit the part information.");
                promptForCurrentStep();
            } else {
                speak("Please say 'save' to save this part or 'edit' to make changes.");
            }
            return;
        }
        
        // Skip command for optional fields
        if (text === 'skip' || text === 'unknown') {
            const stepObj = workflowSteps.find(step => step.id === currentStep);
            if (stepObj && stepObj.optional) {
                // Skip this field and move to next step
                moveToNextStep();
                return;
            }
        }
        
        // Process the input based on current step
        processStepInput(text);
    }
    
    // Process input for the current step
    function processStepInput(text) {
        const stepObj = workflowSteps.find(step => step.id === currentStep);
        if (!stepObj) return;
        
        let value = text;
        let isValid = true;
        let formattedValue = '';
        
        // Format and validate based on field type
        switch (stepObj.id) {
            case 'name':
                // Capitalize each word
                value = text.split(' ').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1)
                ).join(' ');
                formattedValue = `"${value}"`;
                break;
                
            case 'number':
                // Remove spaces and special characters
                value = text.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
                formattedValue = `"${value}"`;
                break;
                
            case 'condition':
                // Map to valid condition values
                if (text.includes('new')) {
                    value = 'new';
                    formattedValue = "New";
                } else if (text.includes('good')) {
                    value = 'used_good';
                    formattedValue = "Used - Good condition";
                } else if (text.includes('fair')) {
                    value = 'used_fair';
                    formattedValue = "Used - Fair condition";
                } else if (text.includes('poor')) {
                    value = 'used_poor';
                    formattedValue = "Used - Poor condition";
                } else {
                    isValid = false;
                    speak("Please specify a valid condition: new, used good, used fair, or used poor.");
                }
                break;
                
            case 'price':
            case 'cost':
                // Extract numeric value
                const priceMatch = text.match(/\d+(\.\d+)?/);
                if (priceMatch) {
                    value = parseFloat(priceMatch[0]);
                    formattedValue = `$${value.toFixed(2)}`;
                } else if (text === 'zero' || text === '0') {
                    value = 0;
                    formattedValue = "$0.00";
                } else {
                    isValid = false;
                    speak(`Please specify a valid ${stepObj.id}.`);
                }
                break;
                
            case 'storage':
                // Try to find matching storage location
                const storageSelect = document.querySelector('select[name="storage_id"]');
                if (storageSelect) {
                    const options = Array.from(storageSelect.options);
                    const match = options.find(option => 
                        option.text.toLowerCase().includes(text.toLowerCase())
                    );
                    
                    if (match) {
                        value = match.value;
                        formattedValue = match.text;
                    } else {
                        isValid = false;
                        speak("I couldn't find that storage location. Please try again or say a different location.");
                    }
                }
                break;
        }
        
        if (isValid) {
            // Store the value
            partFormData[stepObj.field] = value;
            
            // Confirm the input
            speak(`Got it. ${formattedValue} for ${stepObj.id}.`);
            
            // Move to the next step
            moveToNextStep();
        }
    }
    
    // Move to the next step in the workflow
    function moveToNextStep() {
        const currentIndex = workflowSteps.findIndex(step => step.id === currentStep);
        if (currentIndex < workflowSteps.length - 1) {
            currentStep = workflowSteps[currentIndex + 1].id;
            promptForCurrentStep();
        } else {
            // We're at the end, shouldn't happen but just in case
            currentStep = 'confirm';
            promptForCurrentStep();
        }
    }
    
    // Prompt the user for the current step
    function promptForCurrentStep() {
        const stepObj = workflowSteps.find(step => step.id === currentStep);
        if (stepObj) {
            speak(stepObj.prompt);
            updateStatusMessage(`Listening for: ${stepObj.prompt}`, 'listening');
        }
    }
    
    // Start guided voice mode
    function startGuidedMode() {
        // Check if we're on a part form page
        const partForm = document.getElementById('part-form');
        const atvIdField = document.querySelector('input[name="atv_id"]');
        
        if (!partForm || !atvIdField) {
            alert('Guided voice mode can only be used on the Add Part page.');
            return;
        }
        
        // Get the current ATV ID
        currentAtvId = atvIdField.value;
        if (!currentAtvId) {
            alert('Please select an ATV first.');
            return;
        }
        
        // Initialize guided mode
        isInGuidedMode = true;
        currentStep = workflowSteps[0].id;
        partFormData = {};
        partsAdded = 0;
        
        // Update UI
        const guidedBtn = document.getElementById('guided-voice-btn');
        if (guidedBtn) {
            guidedBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Exit Guided Mode';
            guidedBtn.classList.remove('btn-success');
            guidedBtn.classList.add('btn-danger');
        }
        
        // Create or update the status panel
        createOrUpdateStatusPanel();
        
        // Welcome message
        const atv = document.querySelector('.card-header h5');
        const atvName = atv ? atv.textContent : 'this ATV';
        
        speak(`Starting guided voice mode for ${atvName}. I'll help you add parts quickly. Let's begin.`);
        
        // Start the first step after a short pause
        setTimeout(() => {
            promptForCurrentStep();
            
            // Start recognition
            try {
                recognition.start();
            } catch (e) {
                console.error('Recognition error', e);
            }
        }, 2500);
    }
    
    // Exit guided voice mode
    function exitGuidedMode() {
        isInGuidedMode = false;
        
        // Update UI
        const guidedBtn = document.getElementById('guided-voice-btn');
        if (guidedBtn) {
            guidedBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Guided Voice Mode';
            guidedBtn.classList.remove('btn-danger');
            guidedBtn.classList.add('btn-success');
        }
        
        // Final message
        if (partsAdded > 0) {
            speak(`Exiting guided mode. You've added ${partsAdded} parts.`);
        } else {
            speak('Exiting guided mode.');
        }
        
        // Remove status panel
        const statusPanel = document.getElementById('guided-voice-status-panel');
        if (statusPanel) {
            statusPanel.remove();
        }
        
        // Stop recognition
        try {
            recognition.stop();
        } catch (e) {
            console.error('Recognition stop error', e);
        }
    }
    
    // Save the current part
    function savePart() {
        // Get the form
        const form = document.getElementById('part-form');
        if (!form) return;
        
        // Fill in the form fields
        for (const [field, value] of Object.entries(partFormData)) {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                input.value = value;
            }
        }
        
        // Submit the form
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            speak("Saving part now.");
            updateStatusMessage("Saving part...", "success");
            
            // Submit the form
            submitBtn.click();
            
            // Increment counter
            partsAdded++;
            
            // Reset for next part
            setTimeout(() => {
                if (isInGuidedMode) {
                    // Check if we're still on the form page (submission might have redirected)
                    if (document.getElementById('part-form')) {
                        // Clear form data for next part
                        partFormData = {};
                        currentStep = workflowSteps[0].id;
                        
                        speak(`Part saved successfully! That's ${partsAdded} parts added. Let's add another part.`);
                        promptForCurrentStep();
                    } else {
                        // We've been redirected, exit guided mode
                        exitGuidedMode();
                    }
                }
            }, 1500);
        }
    }
    
    // Text-to-speech function
    function speak(text) {
        if (synth.speaking) {
            synth.cancel();
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.1;  // Slightly faster than normal
        synth.speak(utterance);
    }
    
    // Update the status message in the panel
    function updateStatusMessage(message, status) {
        const statusMsg = document.getElementById('guided-voice-status-message');
        if (statusMsg) {
            statusMsg.textContent = message;
            
            // Update styling based on status
            statusMsg.className = 'mt-2';
            if (status === 'error') {
                statusMsg.classList.add('text-danger');
            } else if (status === 'success') {
                statusMsg.classList.add('text-success');
            } else if (status === 'listening') {
                statusMsg.classList.add('text-primary');
            }
        }
    }
    
    // Create or update the status panel
    function createOrUpdateStatusPanel() {
        let panel = document.getElementById('guided-voice-status-panel');
        
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'guided-voice-status-panel';
            panel.className = 'card bg-light mb-3';
            
            const header = document.createElement('div');
            header.className = 'card-header d-flex justify-content-between align-items-center';
            header.innerHTML = '<h6><i class="fas fa-microphone-alt"></i> Guided Voice Mode Active</h6>';
            
            const body = document.createElement('div');
            body.className = 'card-body';
            
            const progressContainer = document.createElement('div');
            progressContainer.className = 'progress mb-3';
            progressContainer.style.height = '25px';
            
            const progressBar = document.createElement('div');
            progressBar.id = 'guided-voice-progress';
            progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', '0');
            progressBar.setAttribute('aria-valuemin', '0');
            progressBar.setAttribute('aria-valuemax', '100');
            
            progressContainer.appendChild(progressBar);
            
            const statusMsg = document.createElement('p');
            statusMsg.id = 'guided-voice-status-message';
            statusMsg.className = 'mt-2';
            statusMsg.textContent = 'Starting guided mode...';
            
            const commandsList = document.createElement('div');
            commandsList.className = 'mt-3 small';
            commandsList.innerHTML = `
                <p><strong>Available commands:</strong></p>
                <ul>
                    <li><strong>skip</strong> - Skip optional fields</li>
                    <li><strong>exit</strong> or <strong>quit</strong> - Exit guided mode</li>
                    <li><strong>switch atv</strong> - Exit and select a different ATV</li>
                    <li><strong>edit</strong> - Go back and edit part info (during confirmation)</li>
                </ul>
            `;
            
            body.appendChild(progressContainer);
            body.appendChild(statusMsg);
            body.appendChild(commandsList);
            
            panel.appendChild(header);
            panel.appendChild(body);
            
            // Add to the form
            const form = document.getElementById('part-form');
            if (form) {
                form.parentNode.insertBefore(panel, form);
            }
        }
        
        // Reset progress bar
        const progressBar = document.getElementById('guided-voice-progress');
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', '0');
            updateProgressBar(0);
        }
    }
    
    // Update the progress bar
    function updateProgressBar(step) {
        const progressBar = document.getElementById('guided-voice-progress');
        if (!progressBar) return;
        
        const totalSteps = workflowSteps.length;
        const currentIndex = workflowSteps.findIndex(s => s.id === currentStep);
        const percent = Math.round((currentIndex / (totalSteps - 1)) * 100);
        
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressBar.textContent = `${percent}% (Step ${currentIndex + 1} of ${totalSteps})`;
    }
    
    // Add the guided mode button to the page
    function addGuidedModeButton() {
        // Only add to part form pages
        const partForm = document.getElementById('part-form');
        if (!partForm) return;
        
        // Find a good place to add the button
        const formTitle = partForm.querySelector('.card-header');
        if (!formTitle) return;
        
        // Create button container if needed
        let buttonContainer = formTitle.querySelector('.d-flex');
        if (!buttonContainer) {
            buttonContainer = document.createElement('div');
            buttonContainer.className = 'd-flex justify-content-between align-items-center';
            
            // Get the form title
            const title = formTitle.innerHTML;
            
            // Clear and replace content
            formTitle.innerHTML = '';
            
            // Create title element
            const titleEl = document.createElement('h5');
            titleEl.innerHTML = title;
            
            // Add elements to container
            buttonContainer.appendChild(titleEl);
            formTitle.appendChild(buttonContainer);
        }
        
        // Create the guided voice button
        const guidedBtn = document.createElement('button');
        guidedBtn.type = 'button';
        guidedBtn.id = 'guided-voice-btn';
        guidedBtn.className = 'btn btn-success';
        guidedBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Guided Voice Mode';
        
        // Add click event handler
        guidedBtn.addEventListener('click', function() {
            if (isInGuidedMode) {
                exitGuidedMode();
            } else {
                startGuidedMode();
            }
        });
        
        // Add button to the container
        buttonContainer.appendChild(guidedBtn);
    }
    
    // Update progress bar when step changes
    const originalStep = currentStep;
    Object.defineProperty(window, 'currentStep', {
        set: function(value) {
            const oldValue = currentStep;
            currentStep = value;
            updateProgressBar();
        },
        get: function() {
            return currentStep;
        }
    });
});
