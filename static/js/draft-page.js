document.addEventListener('DOMContentLoaded', function() {
    // Draft search functionality
    const searchInput = document.querySelector('.draft-search input');
    const draftsContainer = document.querySelector('.drafts-container');
    const draftCards = document.querySelectorAll('.draft-card');

    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            const searchTerm = this.value.toLowerCase();

            // If using server-side filtering, we'd submit the form on Enter key
            if (e.key === 'Enter') {
                this.closest('form').submit();
                return;
            }

            // If we're doing client-side filtering
            if (draftCards.length > 0 && !this.closest('form')) {
                draftCards.forEach(card => {
                    const draftName = card.querySelector('.draft-name').textContent.toLowerCase();
                    const draftExcerpt = card.querySelector('.draft-excerpt').textContent.toLowerCase();

                    if (draftName.includes(searchTerm) || draftExcerpt.includes(searchTerm)) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        });
    }

    // Draft filter functionality
    const filterSelect = document.querySelector('.draft-filter select');

    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            // If using server-side filtering (which is preferable), submit the form
            if (this.closest('form')) {
                this.closest('form').submit();
                return;
            }

            // If we're doing client-side filtering
            const filterValue = this.value;

            if (draftCards.length > 0) {
                draftCards.forEach(card => {
                    const status = card.querySelector('.draft-status').classList[1];

                    if (filterValue === 'all' || status === filterValue) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
        });
    }

    // Delete draft confirmation
    const deleteButtons = document.querySelectorAll('.btn-delete');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // If this is a link to the delete confirmation page, let it proceed
            if (this.tagName === 'A' && this.href) {
                return;
            }

            // Otherwise show a confirm dialog
            if (!confirm('هل أنت متأكد من حذف هذه المسودة؟')) {
                e.preventDefault();
            }
        });
    });

    // Pagination active state
    const paginationButtons = document.querySelectorAll('.pagination-btn');

    if (paginationButtons.length > 0) {
        // The current page button should already have the 'active' class in the HTML

        // Add click handler for smooth transitions
        paginationButtons.forEach(button => {
            if (!button.classList.contains('active') && button.tagName === 'A') {
                button.addEventListener('click', function(e) {
                    // Don't add this for links that are going to different pages
                    if (this.getAttribute('href').includes('page=')) {
                        return;
                    }

                    e.preventDefault();

                    // Remove active class from all buttons
                    paginationButtons.forEach(btn => btn.classList.remove('active'));

                    // Add active class to clicked button
                    this.classList.add('active');

                    // Get the target page from the href
                    const targetPage = this.getAttribute('href');

                    // Fade out drafts container
                    draftsContainer.style.opacity = '0';

                    // Navigate to the new page after fade out
                    setTimeout(() => {
                        window.location.href = targetPage;
                    }, 300);
                });
            }
        });
    }

    // Create draft button animation
    const createDraftBtn = document.querySelector('.create-draft');

    if (createDraftBtn) {
        createDraftBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
        });

        createDraftBtn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    }
});