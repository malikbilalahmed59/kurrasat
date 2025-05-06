document.addEventListener('DOMContentLoaded', function() {
    const languageToggle = document.getElementById('lang-toggle');
    const languageText = document.getElementById('lang-toggle-text');

    if (languageToggle && languageText) {
        // Function to toggle language
        function toggleLanguage() {
            // This function will be called when the language toggle button is clicked
            // The form with the set_language URL in base.html will handle the actual language switching
            document.getElementById('language-form').submit();
        }

        // Expose the function globally
        window.toggleLanguage = toggleLanguage;

        // Add click handler
        languageToggle.addEventListener('click', toggleLanguage);
    }

    // Language buttons in profile settings
    const langButtons = document.querySelectorAll('.lang-btn');
    langButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            langButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Submit the closest form (which would be the language selection form)
            this.closest('form').submit();
        });
    });
});