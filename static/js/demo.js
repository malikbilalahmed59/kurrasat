{% extends 'base.html' %}
{% load static %}
{% load i18n %}

{% block title %}{% trans "كُرّاس - تطوير المستند" %}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'style/development.css' %}" />
{% endblock %}

{% block extra_head %}
<!-- Add user ID for WebSocket authentication -->
<meta name="user-id" content="{{ request.user.id }}">
{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="development-hero">
  <div class="container">
    <div class="hero-content">
      <h1>{% trans "تطوير المستند" %}</h1>
      <p>{% trans "قم بتحميل ملفك وتحليل جودته للحصول على تقرير مفصل" %}</p>
      <div class="breadcrumb">
        <a href="{% url 'core:index' %}">{% trans "الرئيسية" %}</a>
        <span class="separator">/</span>
        <span class="current">{% trans "تطوير المستند" %}</span>
      </div>
    </div>
  </div>
  <!-- Floating Circles -->
  <div class="floating-circle circle-1"></div>
  <div class="floating-circle circle-2"></div>
  <div class="floating-circle circle-3"></div>
</section>

<!-- Development Section -->
<section class="development-section">
  <div class="container">
    <div class="development-container">
      <!-- Right Side - Upload Form -->
      <div class="upload-form-container">
        <div class="form-card">
          <div class="form-header">
            <h2>{% trans "تحميل ملف للتطوير" %}</h2>
            <p>{% trans "يرجى إدخال تفاصيل الملف وتحميله للتحليل" %}</p>
          </div>
          <form id="development-form" class="development-form" method="post" action="{% url 'documents:development' %}" enctype="multipart/form-data">
            {% csrf_token %}

            <div class="form-group">
              <label for="file-title">{% trans "عنوان الملف" %}</label>
              <input
                type="text"
                id="file-title"
                name="file-title"
                placeholder="{% trans 'أدخل عنوان الملف' %}"
                required
              />
              <div class="error-message" id="title-error"></div>
            </div>

            <div class="form-group">
              <label for="file-description">{% trans "وصف الملف" %}</label>
              <textarea
                id="file-description"
                name="file-description"
                placeholder="{% trans 'أدخل وصفًا موجزًا للملف' %}"
                rows="4"
                required
              ></textarea>
              <div class="error-message" id="description-error"></div>
            </div>

            <div class="form-group">
              <label>{% trans "تحميل الملف" %}</label>
              <div class="file-upload-container">
                <div class="file-upload-area" id="file-upload-area">
                  <input
                    type="file"
                    id="file-upload"
                    name="file"
                    class="file-input"
                    accept=".pdf,.doc,.docx,.txt"
                    required
                  />
                  <div class="upload-icon">
                    <i class="fas fa-cloud-upload-alt"></i>
                  </div>
                  <div class="upload-text">
                    <p>{% trans "اسحب الملف هنا أو انقر للتحميل" %}</p>
                    <span>{% trans "PDF, DOC, DOCX, TXT (الحد الأقصى: 10MB)" %}</span>
                  </div>
                </div>
                <div class="selected-file" id="selected-file">
                  <div class="file-info">
                    <i class="fas fa-file-alt file-icon"></i>
                    <div class="file-details">
                      <p class="file-name" id="selected-file-name">
                        {% trans "لم يتم اختيار ملف" %}
                      </p>
                      <p class="file-size" id="selected-file-size"></p>
                    </div>
                  </div>
                  <button
                    type="button"
                    class="remove-file"
                    id="remove-file"
                  >
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
              <div class="error-message" id="file-error"></div>
            </div>

            <div class="form-actions">
              <button
                type="submit"
                class="btn btn-primary btn-lg btn-block"
                id="analyze-button"
              >
                <i class="fas fa-check"></i> {% trans "تحليل الملف" %}
              </button>

            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Analysis Process Section -->
<section class="process-section">
  <div class="container">
    <div class="section-header">
      <h2>{% trans "كيف يعمل تحليل الجودة؟" %}</h2>
      <p>{% trans "عملية بسيطة من 4 خطوات لتحسين جودة مستنداتك" %}</p>
    </div>
    <div class="process-steps">
      <div class="process-step">
        <div class="step-icon">
          <i class="fas fa-upload"></i>
        </div>
        <div class="step-content">
          <h3>{% trans "تحميل الملف" %}</h3>
          <p>{% trans "قم بتحميل المستند الذي ترغب في تحليله وتحسينه" %}</p>
        </div>
      </div>
      <div class="process-step">
        <div class="step-icon">
          <i class="fas fa-search"></i>
        </div>
        <div class="step-content">
          <h3>{% trans "التحليل" %}</h3>
          <p>
            {% trans "يقوم النظام بتحليل المستند وتقييم جودته بناءً على معايير محددة" %}
          </p>
        </div>
      </div>
      <div class="process-step">
        <div class="step-icon">
          <i class="fas fa-chart-bar"></i>
        </div>
        <div class="step-content">
          <h3>{% trans "النتائج" %}</h3>
          <p>{% trans "عرض نتائج التحليل مع تقييم مفصل واقتراحات للتحسين" %}</p>
        </div>
      </div>
      <div class="process-step">
        <div class="step-icon">
          <i class="fas fa-file-pdf"></i>
        </div>
        <div class="step-content">
          <h3>{% trans "التقرير" %}</h3>
          <p>{% trans "تحميل تقرير PDF مفصل يمكنك استخدامه لتحسين المستند" %}</p>
        </div>
      </div>
    </div>
  </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
// Embedded JavaScript for development.html
document.addEventListener('DOMContentLoaded', function() {
  // Get all necessary elements
  const form = document.getElementById('development-form');
  const fileInput = document.getElementById('file-upload');
  const fileUploadArea = document.getElementById('file-upload-area');
  const selectedFile = document.getElementById('selected-file');
  const selectedFileName = document.getElementById('selected-file-name');
  const selectedFileSize = document.getElementById('selected-file-size');
  const removeFileBtn = document.getElementById('remove-file');
  const analyzeBtn = document.getElementById('analyze-button');
  const fileError = document.getElementById('file-error');
  const titleError = document.getElementById('title-error');
  const descriptionError = document.getElementById('description-error');
  const titleInput = document.getElementById('file-title');
  const descriptionInput = document.getElementById('file-description');

  // Only proceed if we have the form and file input
  if (form && fileInput) {
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
        fileError.textContent = 'حجم الملف كبير جدًا. الحد الأقصى هو 10 ميجابايت.';
        fileInput.value = ''; // Clear the file input
        return;
      }

      // Check file type
      const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

      if (!allowedTypes.some(ext => fileExt.endsWith(ext))) {
        fileError.textContent = 'نوع الملف غير مدعوم. يرجى تحميل PDF, DOC, DOCX, أو TXT';
        fileInput.value = ''; // Clear the file input
        return;
      }

      // Clear any previous errors
      fileError.textContent = '';

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
        fileError.textContent = '';
      });
    }

    // Form validation and submission
    form.addEventListener('submit', function(event) {
      let isValid = true;

      // Validate file
      if (!fileInput.files || fileInput.files.length === 0) {
        fileError.textContent = 'يرجى اختيار ملف';
        isValid = false;
      }

      // Validate title
      if (!titleInput.value.trim()) {
        titleError.textContent = 'يرجى إدخال عنوان الملف';
        isValid = false;
      } else {
        titleError.textContent = '';
      }

      // Validate description
      if (!descriptionInput.value.trim()) {
        descriptionError.textContent = 'يرجى إدخال وصف الملف';
        isValid = false;
      } else {
        descriptionError.textContent = '';
      }

      if (!isValid) {
        event.preventDefault();
        // Find first error and scroll to it
        const firstError = document.querySelector('.error-message:not(:empty)');
        if (firstError) {
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
      }

      // If form is valid and we want to use WebSockets, let's handle it with AJAX
      event.preventDefault();

      // Create FormData for AJAX submission
      const formData = new FormData(form);

      // Show loading state
      analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحليل...';
      analyzeBtn.disabled = true;

      // Send form data via AJAX
      fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Connect to WebSocket for streaming analysis
          connectToWebSocket(data.doc_id);

        } else {
          // Show error
          analyzeBtn.innerHTML = '<i class="fas fa-check"></i> تحليل الملف';

          analyzeBtn.disabled = false;

          if (data.error) {
            alert(data.error);
          }
        }
      })
      .catch(error => {
        console.error('Error submitting form:', error);
        analyzeBtn.innerHTML = '<i class="fas fa-check"></i> تحليل الملف';
        analyzeBtn.disabled = false;
        alert('حدث خطأ أثناء معالجة الطلب. يرجى المحاولة مرة أخرى.');
      });
    });

    // WebSocket connection function
    function connectToWebSocket(docId) {
      // Get current protocol (ws: or wss:)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/documents/analyze/${docId}/`;

      // Create WebSocket connection
      const socket = new WebSocket(wsUrl);

      // Create or get results container
      let improvementSuggestions = document.getElementById('improvement-suggestions');
      let suggestionsList;
      let downloadContainer;
      console.log(suggestionsList)

      if (!improvementSuggestions) {
        // Create new results section if it doesn't exist
        const resultsSection = document.createElement('section');
        document.querySelector('.development-container').after(resultsSection);

        improvementSuggestions = document.createElement('div');
        improvementSuggestions.id = 'improvement-suggestions';
        improvementSuggestions.className = 'improvement-suggestions';

        const heading = document.createElement('h3');
        heading.textContent = 'اقتراحات للتحسين';
        improvementSuggestions.appendChild(heading);

        suggestionsList = document.createElement('div');
        suggestionsList.id = 'suggestions-list';
        suggestionsList.className = 'suggestions-list';
        improvementSuggestions.appendChild(suggestionsList);

        downloadContainer = document.createElement('div');
        downloadContainer.className = 'download-report-container';
        downloadContainer.style = 'margin-top: 20px; text-align: center; display: none;';
        improvementSuggestions.appendChild(downloadContainer);

        resultsSection.appendChild(improvementSuggestions);
      } else {
        suggestionsList = document.getElementById('suggestions-list');
        downloadContainer = improvementSuggestions.querySelector('.download-report-container');
      }

      // Show initial loading message
      suggestionsList.innerHTML = '<p>جاري تحليل المستند...</p>';

      // WebSocket event handlers
      socket.onopen = function(e) {
        console.log('WebSocket connection established');

        // Get user ID from meta tag
        const userId = document.querySelector('meta[name="user-id"]')?.getAttribute('content');

        // Send request to analyze the document
        socket.send(JSON.stringify({
          action: 'analyze_document',
          doc_id: docId,
          user_id: userId
        }));
      };

      socket.onmessage = function(e) {
        const data = JSON.parse(e.data);

        switch (data.type) {
          case 'analysis_started':
            suggestionsList.innerHTML = '<p>' + data.message + '</p>';
            break;

          case 'analysis_chunk':
            // Replace loading message with first chunk
            if (suggestionsList.innerHTML.includes('جاري تحليل المستند')) {
              suggestionsList.innerHTML = '';
            }

            // Add incoming content
            suggestionsList.innerHTML += data.content;

            // Auto-scroll to see new content
            improvementSuggestions.scrollIntoView({ behavior: 'smooth', block: 'end' });
            break;

          case 'analysis_complete':
            // Show download button
            if (downloadContainer) {
              downloadContainer.style.display = 'block';
              downloadContainer.innerHTML = `
                <a href="/documents/document_download/${docId}/" class="btn btn-primary">
                  <i class="fas fa-download"></i> تحميل التقرير
                </a>
              `;
            }

            // Reset analyze button
            analyzeBtn.innerHTML = ` <a href="{% static 'js/utils/contract_1745247386.docx' %}" class="btn btn-outline">
        <i class="fas fa-download"></i> {% trans "تنزيل" %}
      </a>`;
            analyzeBtn.disabled = false;
            break;

          case 'error':
            suggestionsList.innerHTML = '<p class="error">' + data.message + '</p>';

            // Reset analyze button
            analyzeBtn.innerHTML = '<i class="fas fa-check"></i> تحليل الملف';
            analyzeBtn.disabled = false;
            break;
        }
      };

      socket.onclose = function(e) {
        console.log('WebSocket connection closed');

        // If it was closed unexpectedly and analysis was in progress
        if (suggestionsList.innerHTML.includes('جاري تحليل المستند')) {
          suggestionsList.innerHTML += '<p class="error">انقطع الاتصال. يرجى المحاولة مرة أخرى.</p>';

          // Reset analyze button
          analyzeBtn.innerHTML = '<i class="fas fa-check"></i> تحليل الملف';
          analyzeBtn.disabled = false;
        }
      };

      socket.onerror = function(e) {
        console.error('WebSocket error:', e);
        suggestionsList.innerHTML = '<p class="error">حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.</p>';

        // Reset analyze button
        analyzeBtn.innerHTML = '<i class="fas fa-check"></i> تحليل الملف';
        analyzeBtn.disabled = false;
      };
    }
  }
});
</script>
{% endblock %}