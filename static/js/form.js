/**
 * RentungFX VIP Registration Form
 * Client-side form validation and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Security console message
    console.log('%c🔒 RentungFX VIP Registration Form\n%cThis is a secure registration form. Please do not paste any code here.', 
               'color: #1a472a; font-size: 16px; font-weight: bold;', 
               'color: #666; font-size: 12px;');
    console.log('✅ RentungFX VIP Registration Form initialized successfully');

    // Form elements with null checks
    const form = document.getElementById('registrationForm');
    const submitBtn = document.getElementById('submitBtn');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const loadingState = document.getElementById('loadingState');
    
    // Exit early if essential elements are missing
    if (!form) {
        console.warn('Registration form not found, exiting form initialization');
        return;
    }
    
    if (!nextBtn || !prevBtn || !submitBtn) {
        console.warn('Some form navigation elements not found, but continuing with available elements');
    }
    
    // Step elements
    const formSteps = document.querySelectorAll('.form-step');
    const progressText = document.getElementById('progressText');
    const progressBarFill = document.getElementById('progressBarFill');
    
    // Current step tracker
    let currentStep = 1;
    const totalSteps = 3;
    
    // Input elements for step 1
    const fullNameInput = document.getElementById('full_name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone_number');
    
    // Input elements for step 2
    const brokerageInput = document.getElementById('brokerage_name');
    const depositInput = document.getElementById('deposit_amount');
    const clientIdInput = document.getElementById('client_id');
    
    // Validation patterns
    const patterns = {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        name: /^[\p{L}\s.'-]{2,50}$/u
    };

    // Error messages (Malay only)
    const errorMessages = {
        required: 'Ruang ini wajib diisi',
        email: 'Email tak betul. Cuba tulis macam nama@gmail.com',
        name: 'Nama tak betul. Tulis nama penuh (2-50 huruf sahaja)',
        minLength: 'Kurang panjang sikit'
    };

    // Use Malay messages only
    const messages = errorMessages;



    /**
     * Step Navigation Functions
     */
    function showStep(step) {
        // Hide all steps
        formSteps.forEach(stepDiv => {
            stepDiv.style.display = 'none';
        });
        
        // Show current step
        const currentStepDiv = document.getElementById(`step-${step}`);
        if (currentStepDiv) {
            currentStepDiv.style.display = 'block';
        }
        
        // Update progress indicator
        const stepLabels = ['Maklumat Diri', 'Info Brokerage & Deposit', 'Bukti Deposit'];
        if (progressText) {
            progressText.textContent = `Langkah ${step} daripada 3: ${stepLabels[step - 1]}`;
        }
        
        // Update step indicators
        const stepIndicators = document.querySelectorAll('.step-indicator');
        stepIndicators.forEach((indicator, index) => {
            const stepNumber = index + 1;
            indicator.classList.remove('active', 'completed');
            
            if (stepNumber === step) {
                indicator.classList.add('active');
            } else if (stepNumber < step) {
                indicator.classList.add('completed');
            }
        });
        
        // Update progress bar
        if (progressBarFill) {
            const progressPercentage = (step / totalSteps) * 100;
            progressBarFill.style.width = `${progressPercentage}%`;
        }
        
        // Update navigation buttons with null checks
        if (prevBtn && nextBtn && submitBtn) {
            if (step === 1) {
                prevBtn.style.display = 'none';
                nextBtn.style.display = 'block';
                submitBtn.style.display = 'none';
            } else if (step === totalSteps) {
                prevBtn.style.display = 'block';
                nextBtn.style.display = 'none';
                submitBtn.style.display = 'block';
            } else {
                prevBtn.style.display = 'block';
                nextBtn.style.display = 'block';
                submitBtn.style.display = 'none';
            }
        }
    }
    
    function validateCurrentStep() {
        let isValid = true;
        
        if (currentStep === 1) {
            // Validate step 1: Personal information
            isValid = validateField(fullNameInput, true) && 
                     validateField(emailInput, true) && 
                     validateField(phoneInput, true);
        } else if (currentStep === 2) {
            // Validate step 2: Brokerage information
            isValid = validateField(brokerageInput, true) && 
                     validateField(depositInput, true) && 
                     validateField(clientIdInput, true);
        }
        // Step 3 (file uploads) is optional, so always valid
        
        return isValid;
    }
    
    // Next button click handler
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (validateCurrentStep()) {
                if (currentStep < totalSteps) {
                    currentStep++;
                    showStep(currentStep);
                }
            }
        });
    }
    
    // Previous button click handler
    if (prevBtn) {
        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (currentStep > 1) {
                currentStep--;
                showStep(currentStep);
            }
        });
    }
    
    // Initialize step display
    showStep(currentStep);

    /**
     * Validate individual field
     */
    function validateField(field, showError = true) {
        const value = field.value.trim();
        const fieldName = field.name;
        let isValid = true;
        let errorMessage = '';

        // Remove existing error styling
        field.classList.remove('is-invalid', 'is-valid');
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }

        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = messages.required;
        }
        // Specific field validations
        else if (value) {
            switch (fieldName) {
                case 'full_name':
                    // Allow any characters for Malaysian names, just check minimum length
                    if (value.length < 2) {
                        isValid = false;
                        errorMessage = messages.name;
                    }
                    break;
                
                case 'email':
                    if (!patterns.email.test(value)) {
                        isValid = false;
                        errorMessage = messages.email;
                    }
                    break;
                

            }
        }

        // Show validation result
        if (showError) {
            if (isValid && value) {
                field.classList.add('is-valid');
            } else if (!isValid) {
                field.classList.add('is-invalid');
                
                // Create error message element
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = errorMessage;
                field.parentNode.appendChild(errorDiv);
            }
        }

        return isValid;
    }

    /**
     * Validate entire form
     */
    function validateForm() {
        let isValid = true;
        
        // Clear previous validation states
        const allFields = form.querySelectorAll('input, select');
        allFields.forEach(field => {
            field.classList.remove('is-invalid', 'is-valid');
            const existingError = field.parentNode.querySelector('.invalid-feedback');
            if (existingError) {
                existingError.remove();
            }
        });
        
        // Validate all required fields
        const requiredFields = form.querySelectorAll('[required]');
        console.log(`Validating ${requiredFields.length} required fields`);
        
        requiredFields.forEach(field => {
            const fieldValid = validateField(field, true);
            console.log(`Field ${field.name}: ${fieldValid ? 'valid' : 'invalid'} (value: "${field.value}")`);
            if (!fieldValid) {
                isValid = false;
            }
        });

        console.log(`Overall form validation: ${isValid ? 'passed' : 'failed'}`);
        return isValid;
    }

    /**
     * Update submit button state
     */
    function updateSubmitButton() {
        const isFormValid = validateForm();
        submitBtn.disabled = !isFormValid;
        
        if (isFormValid) {
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-primary');
        } else {
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-secondary');
        }
    }

    /**
     * Handle form submission
     */
    function handleFormSubmit(event) {
        event.preventDefault();
        
        console.log('Form submission started');
        
        // Debug: Log all form data
        const formData = new FormData(form);
        console.log('=== CLIENT SIDE FORM SUBMISSION DEBUG ===');
        console.log('Form data being submitted:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}: ${value}`);
        }
        console.log('Form action:', form.action);
        console.log('Form method:', form.method);
        
        // Final validation
        if (!validateForm()) {
            console.log('❌ CLIENT-SIDE VALIDATION FAILED');
            console.log('Form will NOT be submitted to server');
            
            // Find and log all validation errors
            const invalidFields = form.querySelectorAll('.is-invalid');
            console.log('Invalid fields found:', invalidFields.length);
            invalidFields.forEach(field => {
                console.log(`  - ${field.name || field.id}: ${field.value}`);
                const errorMsg = field.parentNode.querySelector('.invalid-feedback');
                if (errorMsg) {
                    console.log(`    Error: ${errorMsg.textContent}`);
                }
            });
            
            // Scroll to first error
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                console.log('Scrolling to error:', firstError.name);
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
            return false;
        }

        console.log('✅ CLIENT-SIDE VALIDATION PASSED');
        console.log('Form will be submitted to server now...');

        // Show loading state
        submitBtn.classList.add('d-none');
        if (loadingState) {
            loadingState.classList.remove('d-none');
        }
        
        // Add visual feedback
        const submitContainer = submitBtn.parentElement;
        if (submitContainer && !submitContainer.querySelector('.submission-status')) {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'submission-status text-center mt-2';
            statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Menghantar maklumat...';
            submitContainer.appendChild(statusDiv);
        }

        // Disable all form inputs
        const formInputs = form.querySelectorAll('input, select, button');
        formInputs.forEach(input => {
            input.disabled = true;
        });

        // Ensure all form steps are visible for submission
        formSteps.forEach(step => {
            step.style.display = 'block';
        });
        
        // Add a small delay for better UX
        setTimeout(() => {
            console.log('Submitting form to server...');
            try {
                form.submit();
            } catch (error) {
                console.error('Form submission error:', error);
                // Re-enable form on error
                formInputs.forEach(input => {
                    input.disabled = false;
                });
                submitBtn.classList.remove('d-none');
                if (loadingState) {
                    loadingState.classList.add('d-none');
                }
                // Restore step visibility
                showStep(currentStep);
            }
        }, 500);
    }

    /**
     * Real-time phone number field - just clear validation errors
     */
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            // Clear previous validation state on input
            this.classList.remove('is-invalid', 'is-valid');
            const existingError = this.parentNode.querySelector('.invalid-feedback');
            if (existingError) {
                existingError.remove();
            }
        });
    }

    /**
     * Real-time validation for other fields (only clear errors on input)
     */
    [fullNameInput, emailInput, phoneInput].forEach(input => {
        if (input) {
            input.addEventListener('input', function() {
                // Clear previous validation state on input
                this.classList.remove('is-invalid', 'is-valid');
                const existingError = this.parentNode.querySelector('.invalid-feedback');
                if (existingError) {
                    existingError.remove();
                }
            });
        }
    });

    /**
     * Handle brokerage field changes (only clear errors on input/change)
     */
    [brokerageInput, depositInput, clientIdInput].forEach(input => {
        if (input) {
            const eventType = input.tagName === 'SELECT' ? 'change' : 'input';
            input.addEventListener(eventType, function() {
                // Clear previous validation state on input/change
                this.classList.remove('is-invalid', 'is-valid');
                const existingError = this.parentNode.querySelector('.invalid-feedback');
                if (existingError) {
                    existingError.remove();
                }
            });
        }
    });

    /**
     * Form submission handling
     */
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    /**
     * Auto-focus first field in current step
     */
    function focusFirstFieldInStep() {
        const currentStepDiv = document.getElementById(`step-${currentStep}`);
        if (currentStepDiv) {
            const firstInput = currentStepDiv.querySelector('input[required]');
            if (firstInput && window.innerWidth > 768) {
                setTimeout(() => {
                    firstInput.focus();
                }, 300);
            }
        }
    }
    
    // Focus first field initially
    focusFirstFieldInStep();

    /**
     * Smooth scroll to form errors
     */
    function scrollToError() {
        const firstError = document.querySelector('.alert-danger, .is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }
    }

    // Scroll to errors on page load if any
    if (document.querySelector('.alert-danger')) {
        setTimeout(scrollToError, 300);
    }

    /**
     * Prevent double submission and add better error handling
     */
    let isSubmitting = false;
    if (form) {
        form.addEventListener('submit', function(e) {
            if (isSubmitting) {
                console.log('❌ DOUBLE SUBMISSION PREVENTED');
                e.preventDefault();
                return false;
            }
            console.log('🚀 FORM SUBMISSION INITIATED');
            isSubmitting = true;
            
            // Reset submission flag after 10 seconds as a safety measure
            setTimeout(() => {
                isSubmitting = false;
                console.log('Submission flag reset after timeout');
            }, 10000);
        });
    }

    /**
     * Form input animations
     */
    const formInputs = document.querySelectorAll('.form-control, .form-select');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentNode.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentNode.classList.remove('focused');
            }
        });
        
        // Set initial focused state for inputs with values
        if (input.value) {
            input.parentNode.classList.add('focused');
        }
    });

    /**
     * Keyboard navigation enhancement
     */
    document.addEventListener('keydown', function(e) {
        // Submit form with Ctrl+Enter
        if (e.ctrlKey && e.key === 'Enter' && form) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    /**
     * Copy protection (optional security measure)
     */
    document.addEventListener('selectstart', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return true;
        }
        return false;
    });

    /**
     * Console security message
     */
    if (window.console) {
        console.log(
            '%c🔒 RentungFX VIP Registration Form\n%cThis is a secure registration form. Please do not paste any code here.',
            'color: #1a472a; font-size: 16px; font-weight: bold;',
            'color: #666; font-size: 12px;'
        );
    }

    /**
     * Page visibility handling (prevent form timeout when tab is hidden)
     */
    let pageHidden = false;
    document.addEventListener('visibilitychange', function() {
        pageHidden = document.hidden;
    });

    /**
     * Network status handling
     */
    function handleOnline() {
        console.log('Connection restored');
        // Could show a message that connection is restored
    }

    function handleOffline() {
        console.log('Connection lost');
        // Could show a message about connection loss
    }

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    console.log('✅ RentungFX VIP Registration Form initialized successfully');
});
