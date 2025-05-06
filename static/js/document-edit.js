document.addEventListener('DOMContentLoaded', function() {
    const editForm = document.getElementById('edit-form');

    if (editForm) {
        // Form validation
        editForm.addEventListener('submit', function(e) {
            let isValid = true;

            // Validate title field
            const titleInput = document.getElementById('id_title');
            if (!titleInput.value.trim()) {
                isValid = false;
                titleInput.classList.add('error');

                // Add error message if it doesn't exist
                let errorMsg = titleInput.nextElementSibling;
                if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'error-message';
                    titleInput.parentNode.insertBefore(errorMsg, titleInput.nextElementSibling);
                }
                errorMsg.textContent = 'يرجى إدخال عنوان المستند';
            } else {
                titleInput.classList.remove('error');

                // Remove error message if it exists
                const errorMsg = titleInput.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('error-message')) {
                    errorMsg.textContent = '';
                }
            }

            // Validate description field
            const descriptionInput = document.getElementById('id_description');
            if (!descriptionInput.value.trim()) {
                isValid = false;
                descriptionInput.classList.add('error');

                // Add error message if it doesn't exist
                let errorMsg = descriptionInput.nextElementSibling;
                if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'error-message';
                    descriptionInput.parentNode.insertBefore(errorMsg, descriptionInput.nextElementSibling);
                }
                errorMsg.textContent = 'يرجى إدخال وصف المستند';
            } else {
                descriptionInput.classList.remove('error');

                // Remove error message if it exists
                const errorMsg = descriptionInput.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('error-message')) {
                    errorMsg.textContent = '';
                }
            }

            // Validate content field
            const contentInput = document.getElementById('id_content');
            if (!contentInput.value.trim()) {
                isValid = false;
                contentInput.classList.add('error');

                // Add error message if it doesn't exist
                let errorMsg = contentInput.nextElementSibling;
                if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'error-message';
                    contentInput.parentNode.insertBefore(errorMsg, contentInput.nextElementSibling);
                }
                errorMsg.textContent = 'يرجى إدخال محتوى المستند';
            } else {
                contentInput.classList.remove('error');

                // Remove error message if it exists
                const errorMsg = contentInput.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('error-message')) {
                    errorMsg.textContent = '';
                }
            }

            if (!isValid) {
                e.preventDefault();
            } else {
                // Show loading state
                const submitBtn = editForm.querySelector('button[type="submit"]');
                const btnText = submitBtn.querySelector('.btn-text');

                submitBtn.disabled = true;
                btnText.textContent = 'جاري الحفظ...';
                submitBtn.classList.add('loading');

                // Form will be submitted normally
            }
        });

        // Unsaved changes warning
        let formChanged = false;

        // Track form changes
        const formInputs = editForm.querySelectorAll('input, textarea, select');
        formInputs.forEach(input => {
            input.addEventListener('change', function() {
                formChanged = true;
            });

            if (input.tagName === 'TEXTAREA' || input.type === 'text') {
                input.addEventListener('keyup', function() {
                    formChanged = true;
                });
            }
        });

        // Warn user before leaving page with unsaved changes
        window.addEventListener('beforeunload', function(e) {
            if (formChanged) {
                // Standard text that browsers will show (may be ignored by some browsers)
                const confirmationMessage = 'لديك تغييرات غير محفوظة. هل أنت متأكد من رغبتك في مغادرة الصفحة؟';

                e.returnValue = confirmationMessage; // For Chrome
                return confirmationMessage; // For older browsers
            }
        });

        // Don't show warning when form is submitted
        editForm.addEventListener('submit', function() {
            formChanged = false;
        });

        // Don't show warning for the cancel button
        const cancelBtn = document.querySelector('a.btn-outline');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function(e) {
                if (formChanged) {
                    if (!confirm('لديك تغييرات غير محفوظة. هل أنت متأكد من رغبتك في مغادرة الصفحة؟')) {
                        e.preventDefault();
                    }
                }
            });
        }
    }

    // Add animation classes on page load
    const animateElements = document.querySelectorAll('.animate');

    setTimeout(() => {
        animateElements.forEach(element => {
            element.classList.add('animated');
        });
    }, 100);
});