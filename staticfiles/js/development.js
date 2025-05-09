document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('development-form');
  const fileInput = document.getElementById('file-upload');
    const fileUploadArea = document.getElementById('file-upload-area');
    const selectedFile = document.getElementById('selected-file');
    const selectedFileName = document.getElementById('selected-file-name');
    const selectedFileSize = document.getElementById('selected-file-size');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-button');

    if (developmentForm && fileInput) {
        // Initial state
        selectedFile.style.display = 'none';

        // File drop area functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            fileUploadArea.classList.add('highlight');
        }

        function unhighlight() {
            fileUploadArea.classList.remove('highlight');
        }

        fileUploadArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                fileInput.files = files;
                updateFileInfo(files[0]);
            }
        }

        // File input change handler
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileInfo(this.files[0]);
            }
        });

        // Update file info function
        function updateFileInfo(file) {
            // Check file size (max 10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB in bytes

            if (file.size > maxSize) {
                // Show error
                const fileError = document.getElementById('file-error');
                fileError.textContent = 'حجم الملف كبير جدًا. الحد الأقصى هو 10 ميجابايت.';
                return;
            }

            // Clear any previous errors
            const fileError = document.getElementById('file-error');
            if (fileError) {
                fileError.textContent = '';
            }

            // Update UI
            selectedFileName.textContent = file.name;

            // Format file size
            let fileSize;
            if (file.size < 1024) {
                fileSize = file.size + ' bytes';
            } else if (file.size < 1024 * 1024) {
                fileSize = (file.size / 1024).toFixed(2) + ' KB';
            } else {
                fileSize = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
            }

            selectedFileSize.textContent = fileSize;

            // Show selected file info
            selectedFile.style.display = 'flex';
            fileUploadArea.style.display = 'none';
        }

        // Remove file button
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', function() {
                fileInput.value = '';
                selectedFile.style.display = 'none';
                fileUploadArea.style.display = 'flex';

                // Clear any previous errors
                const fileError = document.getElementById('file-error');
                if (fileError) {
                    fileError.textContent = '';
                }
            });
        }

        // Form validation and submission
        form.addEventListener('submit', function(event) {
    if (!fileInput.files || fileInput.files.length === 0) {
      event.preventDefault();
      document.getElementById('file-error').textContent = 'Please select a file';
      // Scroll to the error
      document.getElementById('file-error').scrollIntoView({behavior: 'smooth'});
    }
  });
    }

    // Improvement suggestions section (for simulating analysis results)
    const analyzeBtnTest = document.getElementById('analyze-button-test');
    const improvementSuggestions = document.getElementById('improvement-suggestions');
    const suggestionsList = document.getElementById('suggestions-list');

    if (analyzeBtnTest && improvementSuggestions && suggestionsList) {
        analyzeBtnTest.addEventListener('click', function() {
            // This is just for demonstration - in the real app, this would come from backend
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحليل...';

            setTimeout(() => {
                // Show suggestions section
                improvementSuggestions.style.display = 'block';

                // Add some sample suggestions
                suggestionsList.innerHTML = `
                    <div class="suggestion-item">
                        <div class="suggestion-icon success">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="suggestion-content">
                            <h4>هيكل المستند</h4>
                            <p>هيكل المستند منظم بشكل جيد ويتبع المعايير المطلوبة.</p>
                        </div>
                    </div>
                    
                    <div class="suggestion-item">
                        <div class="suggestion-icon warning">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="suggestion-content">
                            <h4>المعلومات المالية</h4>
                            <p>بعض المعلومات المالية غير كاملة. يرجى إضافة تفاصيل حول الميزانية المتوقعة والحد الأدنى للعطاءات.</p>
                        </div>
                    </div>
                    
                    <div class="suggestion-item">
                        <div class="suggestion-icon error">
                            <i class="fas fa-times-circle"></i>
                        </div>
                        <div class="suggestion-content">
                            <h4>متطلبات قانونية مفقودة</h4>
                            <p>المستند يفتقر إلى بعض المتطلبات القانونية الضرورية مثل شروط الضمان وإجراءات التحكيم.</p>
                        </div>
                    </div>
                `;

                // Reset button
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-check"></i> تحليل الملف';

                // Scroll to results
                improvementSuggestions.scrollIntoView({ behavior: 'smooth' });
            }, 2000);
        });
    }

    // Download report button
    const downloadReportBtn = document.getElementById('download-report');

    if (downloadReportBtn) {
        downloadReportBtn.addEventListener('click', function() {
            // In a real implementation, this would trigger a request to the server
            // Here we just show a success message
            alert('تم تحميل التقرير بنجاح!');
        });
    }
});