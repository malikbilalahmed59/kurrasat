document.addEventListener('DOMContentLoaded', function() {
    // Profile tabs functionality
    const tabLinks = document.querySelectorAll('.profile-menu li');
    const tabContents = document.querySelectorAll('.profile-tab');

    tabLinks.forEach(tabLink => {
        tabLink.addEventListener('click', function() {
            // Skip if it's the logout or drafts button
            if (this.id === 'logout-btn' || this.id === 'drafts-btn') {
                return;
            }

            // Remove active class from all tabs
            tabLinks.forEach(link => {
                if (link.id !== 'logout-btn' && link.id !== 'drafts-btn') {
                    link.classList.remove('active');
                }
            });

            // Add active class to current tab
            this.classList.add('active');

            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.remove('active');
            });

            // Show current tab content
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Update URL hash
            window.location.hash = tabId;
        });
    });

    // Check URL hash on page load to activate corresponding tab
    const initialTab = window.location.hash.substring(1);
    if (initialTab) {
        const targetTab = document.querySelector(`[data-tab="${initialTab}"]`);
        if (targetTab) {
            targetTab.click();
        }
    }

    // Theme switcher in settings
    const themeButtons = document.querySelectorAll('.theme-btn');
    themeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            themeButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Set theme
            const theme = this.getAttribute('data-theme');
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);

            // Update theme toggle icon in header
            const themeIcon = document.querySelector('.theme-toggle-icon');
            if (theme === 'dark') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        });
    });

    // Profile picture upload
    const avatarInput = document.getElementById('avatar-upload-input');
    const avatarImg = document.getElementById('profile-avatar-img');

    if (avatarInput && avatarImg) {
        avatarInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();

                reader.onload = function(e) {
                    avatarImg.src = e.target.result;

                    // Create a form to submit the new avatar
                    const formData = new FormData();
                    formData.append('profile_image', avatarInput.files[0]);
                    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

                    // Submit using fetch API
                    fetch(window.location.pathname, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Show success message
                            const message = document.createElement('div');
                            message.className = 'message success';
                            message.textContent = 'تم تحديث الصورة الشخصية بنجاح';
                            document.querySelector('.profile-container').prepend(message);

                            // Remove message after 3 seconds
                            setTimeout(() => {
                                message.remove();
                            }, 3000);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
                };

                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Toggle password visibility in security tab
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');

    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;

            // Toggle input type
            if (input.type === 'password') {
                input.type = 'text';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            } else {
                input.type = 'password';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            }
        });
    });

    // Password change form validation
    const passwordChangeForm = document.getElementById('password-change-form');

    if (passwordChangeForm) {
        passwordChangeForm.addEventListener('submit', function(e) {
            const currentPassword = document.getElementById('current-password');
            const newPassword = document.getElementById('new-password');
            const confirmPassword = document.getElementById('confirm-password');

            let isValid = true;

            // Check if all fields are filled
            if (!currentPassword.value) {
                isValid = false;
                currentPassword.classList.add('error');
            } else {
                currentPassword.classList.remove('error');
            }

            if (!newPassword.value) {
                isValid = false;
                newPassword.classList.add('error');
            } else {
                newPassword.classList.remove('error');
            }

            if (!confirmPassword.value) {
                isValid = false;
                confirmPassword.classList.add('error');
            } else {
                confirmPassword.classList.remove('error');
            }

            // Check if passwords match
            if (newPassword.value !== confirmPassword.value) {
                isValid = false;
                confirmPassword.classList.add('error');

                // Show error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error-message';
                errorMsg.textContent = 'كلمتا المرور غير متطابقتين';

                // Remove any existing error messages
                const existingError = confirmPassword.parentNode.querySelector('.error-message');
                if (existingError) {
                    existingError.remove();
                }

                confirmPassword.parentNode.appendChild(errorMsg);
            }

            // Prevent form submission if validation fails
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
});