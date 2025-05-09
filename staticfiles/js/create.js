document.addEventListener('DOMContentLoaded', function() {
    const notebookForm = document.getElementById('notebook-form');

    if (notebookForm) {
        notebookForm.addEventListener('submit', function(e) {
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
                errorMsg.textContent = 'يرجى إدخال اسم الكراسة';
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
                errorMsg.textContent = 'يرجى إدخال أهداف المنافسة';
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
                errorMsg.textContent = 'يرجى إدخال وصف المنافسة';
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
                const submitBtn = notebookForm.querySelector('button[type="submit"]');
                const btnText = submitBtn.querySelector('.btn-text');

                submitBtn.disabled = true;
                btnText.textContent = 'جاري الإنشاء...';
                submitBtn.classList.add('loading');

                // Form will be submitted normally
            }
        });
    }

    // Add animation classes on page load
    const animateElements = document.querySelectorAll('.animate');

    setTimeout(() => {
        animateElements.forEach(element => {
            element.classList.add('animated');
        });
    }, 100);
});