// Add this to document_detail.js
document.addEventListener('DOMContentLoaded', function() {
  // Check if we're on a document detail page with an analyze button
  const analyzeButton = document.getElementById('analyze-document');
  if (!analyzeButton) return;

  const docId = analyzeButton.getAttribute('data-doc-id');
  const userId = analyzeButton.getAttribute('data-user-id');

  const analysisResult = document.getElementById('analysis-result');
  const suggestionsResult = document.getElementById('suggestions-result');
  const analysisStatus = document.getElementById('analysis-status');

  if (!docId || !userId || !analysisResult || !suggestionsResult) return;

  // Connect to WebSocket
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/documents/analyze/${docId}/`;
  let socket;

  function connectWebSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = function(e) {
      console.log('WebSocket connected');

      // Enable analyze button when connection is established
      analyzeButton.disabled = false;
      analyzeButton.addEventListener('click', startAnalysis);
    };

    socket.onmessage = function(e) {
      const data = JSON.parse(e.data);

      switch (data.type) {
        case 'analysis_started':
          analysisStatus.textContent = data.message;
          analysisStatus.classList.add('analyzing');
          analyzeButton.disabled = true;
          break;

        case 'analysis_chunk':
          if (data.section === 'analysis') {
            analysisResult.innerHTML += data.content;
            // Scroll to bottom of analysis container
            analysisResult.scrollTop = analysisResult.scrollHeight;
          } else {
            suggestionsResult.innerHTML += data.content;
            // Scroll to bottom of suggestions container
            suggestionsResult.scrollTop = suggestionsResult.scrollHeight;
          }
          break;

        case 'analysis_complete':
          analysisStatus.textContent = data.message;
          analysisStatus.classList.remove('analyzing');
          analysisStatus.classList.add('complete');
          analyzeButton.disabled = false;

          // Show download button
          const downloadContainer = document.querySelector('.download-report-container');
          if (downloadContainer) {
            downloadContainer.style.display = 'block';
          }
          break;

        case 'error':
          analysisStatus.textContent = data.message;
          analysisStatus.classList.remove('analyzing');
          analysisStatus.classList.add('error');
          analyzeButton.disabled = false;
          break;
      }
    };

    socket.onclose = function(e) {
      console.log('WebSocket disconnected, trying to reconnect in 5 seconds...');
      analyzeButton.disabled = true;
      setTimeout(connectWebSocket, 5000);
    };

    socket.onerror = function(e) {
      console.error('WebSocket error:', e);
      analysisStatus.textContent = 'حدث خطأ في الاتصال';
      analysisStatus.classList.add('error');
    };
  }

  function startAnalysis() {
    // Clear previous results
    analysisResult.innerHTML = '';
    suggestionsResult.innerHTML = '';

    // Send analyze request to WebSocket
    socket.send(JSON.stringify({
      action: 'analyze_document',
      doc_id: docId,
      user_id: userId
    }));
  }

  // Initial WebSocket connection
  connectWebSocket();
});