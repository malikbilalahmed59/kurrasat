document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
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

    // Form validation
    const signupForm = document.getElementById('signupForm');
    const loginForm = document.getElementById('loginForm');

    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            let isValid = true;

            // Username validation
            const username = document.getElementById('id_username');
            const usernameError = document.getElementById('username-error') || document.createElement('div');
            usernameError.className = 'error-message';
            usernameError.id = 'username-error';

            if (username && username.value.trim() === '') {
                isValid = false;
                usernameError.textContent = 'يرجى إدخال اسم المستخدم';
                if (!username.nextElementSibling || username.nextElementSibling.id !== 'username-error') {
                    username.parentNode.appendChild(usernameError);
                }
            } else if (username) {
                usernameError.textContent = '';
            }

            // Email validation
            const email = document.getElementById('id_email');
            const emailError = document.getElementById('email-error') || document.createElement('div');
            emailError.className = 'error-message';
            emailError.id = 'email-error';

            if (email && email.value.trim() === '') {
                isValid = false;
                emailError.textContent = 'يرجى إدخال البريد الإلكتروني';
                if (!email.nextElementSibling || email.nextElementSibling.id !== 'email-error') {
                    email.parentNode.appendChild(emailError);
                }
            } else if (email && !/\S+@\S+\.\S+/.test(email.value)) {
                isValid = false;
                emailError.textContent = 'يرجى إدخال بريد إلكتروني صحيح';
                if (!email.nextElementSibling || email.nextElementSibling.id !== 'email-error') {
                    email.parentNode.appendChild(emailError);
                }
            } else if (email) {
                emailError.textContent = '';
            }

            // Password validation
            const password1 = document.getElementById('id_password1');
            const password1Error = document.getElementById('password1-error') || document.createElement('div');
            password1Error.className = 'error-message';
            password1Error.id = 'password1-error';

            if (password1 && password1.value.trim() === '') {
                isValid = false;
                password1Error.textContent = 'يرجى إدخال كلمة المرور';
                if (!password1.nextElementSibling || password1.nextElementSibling.id !== 'password1-error') {
                    password1.parentNode.appendChild(password1Error);
                }
            } else if (password1 && password1.value.length < 8) {
                isValid = false;
                password1Error.textContent = 'يجب أن تتكون كلمة المرور من 8 أحرف على الأقل';
                if (!password1.nextElementSibling || password1.nextElementSibling.id !== 'password1-error') {
                    password1.parentNode.appendChild(password1Error);
                }
            } else if (password1) {
                password1Error.textContent = '';
            }

            // Confirm password validation
            const password2 = document.getElementById('id_password2');
            const password2Error = document.getElementById('password2-error') || document.createElement('div');
            password2Error.className = 'error-message';
            password2Error.id = 'password2-error';

            if (password2 && password2.value.trim() === '') {
                isValid = false;
                password2Error.textContent = 'يرجى تأكيد كلمة المرور';
                if (!password2.nextElementSibling || password2.nextElementSibling.id !== 'password2-error') {
                    password2.parentNode.appendChild(password2Error);
                }
            } else if (password2 && password1 && password2.value !== password1.value) {
                isValid = false;
                password2Error.textContent = 'كلمة المرور غير متطابقة';
                if (!password2.nextElementSibling || password2.nextElementSibling.id !== 'password2-error') {
                    password2.parentNode.appendChild(password2Error);
                }
            } else if (password2) {
                password2Error.textContent = '';
            }

            // Terms agreement validation
            const terms = document.getElementById('terms');
            const termsError = document.getElementById('termsError');

            if (terms && !terms.checked) {
                isValid = false;
                if (termsError) {
                    termsError.textContent = 'يجب الموافقة على الشروط والأحكام';
                }
            } else if (termsError) {
                termsError.textContent = '';
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            let isValid = true;

            // Username/Email validation
            const username = document.getElementById('id_username');
            const usernameError = document.getElementById('username-error') || document.createElement('div');
            usernameError.className = 'error-message';
            usernameError.id = 'username-error';

            if (username && username.value.trim() === '') {
                isValid = false;
                usernameError.textContent = 'يرجى إدخال اسم المستخدم أو البريد الإلكتروني';
                if (!username.nextElementSibling || username.nextElementSibling.id !== 'username-error') {
                    username.parentNode.appendChild(usernameError);
                }
            } else if (username) {
                usernameError.textContent = '';
            }

            // Password validation
            const password = document.getElementById('id_password');
            const passwordError = document.getElementById('password-error') || document.createElement('div');
            passwordError.className = 'error-message';
            passwordError.id = 'password-error';

            if (password && password.value.trim() === '') {
                isValid = false;
                passwordError.textContent = 'يرجى إدخال كلمة المرور';
                if (!password.nextElementSibling || password.nextElementSibling.id !== 'password-error') {
                    password.parentNode.appendChild(passwordError);
                }
            } else if (password) {
                passwordError.textContent = '';
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    // Google Sign-In
    const googleSignInBtn = document.querySelector('.google-signin-btn');
    if (googleSignInBtn) {
        googleSignInBtn.addEventListener('click', function() {
            // Redirect to Google OAuth URL
            // This would typically be handled by Django's social auth
            console.log('Google sign in clicked');
        });
    }

    // Apple Sign-In
    const appleSignInBtn = document.querySelector('.apple-signin-btn');
    if (appleSignInBtn) {
        appleSignInBtn.addEventListener('click', function() {
            // Redirect to Apple OAuth URL
            // This would typically be handled by Django's social auth
            console.log('Apple sign in clicked');
        });
    }
});