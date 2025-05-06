# views.py with AJAX and WebSocket support
import time

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext as _
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Document, DocumentAnalysis
from .forms import DocumentForm, DocumentAnalysisForm
import os
import json
import os
import random
from django.conf import settings

@login_required
def create_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            messages.success(request, _('Document created successfully!'))
            time.sleep(160)
            with open("output.pdf", "wb") as file:
                file.write(b"")
                file.close()
            return redirect('documents:document_detail', doc_id=document.id)
    else:
        form = DocumentForm()

    return render(request, 'create.html', {'form': form})


@login_required
@ensure_csrf_cookie
@login_required
@ensure_csrf_cookie
def develop_document(request):
    """
    Handle document upload for analysis.
    For AJAX requests, return JSON response.
    For regular requests, render the template with analysis results if available.
    """
    # Import necessary modules
    import os
    import random
    from django.conf import settings

    # Get random document for the download button
    # Use a path that's guaranteed to exist - try STATICFILES_DIRS instead of STATIC_ROOT
    try:
        # First try to use STATICFILES_DIRS if defined
        if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
            for static_dir in settings.STATICFILES_DIRS:
                utils_dir = os.path.join(static_dir, 'js/utils')
                if os.path.exists(utils_dir):
                    break
        # If STATICFILES_DIRS didn't work, try STATIC_ROOT
        elif settings.STATIC_ROOT:
            utils_dir = os.path.join(settings.STATIC_ROOT, 'js/utils')
        # Last resort, use BASE_DIR
        else:
            utils_dir = os.path.join(settings.BASE_DIR, 'static', 'js/utils')

        # Make sure the directory exists
        if os.path.exists(utils_dir):
            doc_files = [f for f in os.listdir(utils_dir)
                         if f.endswith('.doc') or f.endswith('.docx')]
            doc = random.choice(doc_files) if doc_files else "contract_1745247386.docx"
        else:
            doc = "contract_1745247386.docx"  # Default document
    except Exception as e:
        # Fallback if anything fails
        doc = "contract_1745247386.docx"  # Default document

    # Process POST request
    if request.method == 'POST':
        file = request.FILES.get('file')
        title = request.POST.get('file-title')
        description = request.POST.get('file-description')

        if not file:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': _('Please select a file')})
            messages.error(request, _('Please select a file'))
            return render(request, 'development.html', {'doc': doc})

        if not title:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': _('Please enter a title')})
            messages.error(request, _('Please enter a title'))
            return render(request, 'development.html', {'doc': doc})

        # Create the document
        document = Document.objects.create(
            user=request.user,
            title=title,
            description=description,
            file=file
        )

        # If it's an AJAX request, return document ID for WebSocket connection
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'doc_id': document.id,
                'message': _('File uploaded successfully. Starting analysis...')
            })

        # For regular form submissions, start analysis and show results
        try:
            # You would typically trigger analysis here, but now it will be handled by WebSocket
            # For non-AJAX fallback, create an empty analysis to show the UI
            analysis = DocumentAnalysis.objects.create(
                document=document,
                analysis_text=_('Analysis will be provided shortly.'),
                suggestions=_('Please wait while we analyze your document.')
            )
            time.sleep(5)
            return render(request, 'development.html', {'analysis': 'True', 'doc': doc})
        except Exception as e:
            messages.error(request, f"{_('Error during analysis')}: {str(e)}")
            return render(request, 'development.html', {'doc': doc})

    return render(request, 'development.html', {'doc': doc})


@login_required
def document_list(request):
    """Get all documents for the current user with optional filtering"""
    documents = Document.objects.filter(user=request.user)

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(title__icontains=search_query)

    # Handle status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        documents = documents.filter(status=status_filter)

    # Order by most recently updated
    documents = documents.order_by('-updated_at')

    return render(request, 'drafts.html', {'documents': documents})


@login_required
def document_detail(request, doc_id):
    # Import necessary modules
    import os
    import random
    from django.conf import settings

    # Get random document for the download button
    # Use a path that's guaranteed to exist - try STATICFILES_DIRS instead of STATIC_ROOT
    try:
        # First try to use STATICFILES_DIRS if defined
        if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
            for static_dir in settings.STATICFILES_DIRS:
                utils_dir = os.path.join(static_dir, 'js/utils')
                if os.path.exists(utils_dir):
                    break
        # If STATICFILES_DIRS didn't work, try STATIC_ROOT
        elif settings.STATIC_ROOT:
            utils_dir = os.path.join(settings.STATIC_ROOT, 'js/utils')
        # Last resort, use BASE_DIR
        else:
            utils_dir = os.path.join(settings.BASE_DIR, 'static', 'js/utils')

        # Make sure the directory exists
        if os.path.exists(utils_dir):
            # Look for PDF files instead of DOC files
            pdf_files = [f for f in os.listdir(utils_dir)
                         if f.endswith('.pdf')]
            pdf = random.choice(pdf_files) if pdf_files else "sample.pdf"
        else:
            pdf = "sample.pdf"  # Default PDF
    except Exception as e:
        # Fallback if anything fails
        pdf = "sample.pdf"  # Default PDF

    # Get the document and analyses
    document = get_object_or_404(Document, id=doc_id, user=request.user)
    analyses = document.analyses.all().order_by('-analysis_date')

    # Return the template with all context variables
    return render(request, 'document_detail.html', {
        'document': document,
        'analyses': analyses,
        'pdf': pdf  # Pass the random PDF filename
    })

@login_required
def document_edit(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, _('Document updated successfully!'))
            return redirect('documents:document_detail', doc_id=document.id)
    else:
        form = DocumentForm(instance=document)

    return render(request, 'document_edit.html', {'form': form, 'document': document})


@login_required
def document_delete(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    if request.method == 'POST':
        document.delete()
        messages.success(request, _('Document deleted successfully!'))
        return redirect('documents:drafts')

    return render(request, 'document_confirm_delete.html', {'document': document})


@login_required
def document_download(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, user=request.user)

    # If there's a file uploaded, download that
    if document.file:
        file_path = document.file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response

    # If there's an analysis, generate a PDF report
    analyses = document.analyses.all().order_by('-analysis_date')
    if analyses.exists():
        analysis = analyses.first()

        # Here you would typically generate a PDF report
        # For simplicity, we'll just create a text file
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{document.title}_analysis.txt"'

        # Write content to response
        response.write(f"Title: {document.title}\n")
        response.write(f"Description: {document.description}\n\n")
        response.write(f"Analysis:\n{analysis.analysis_text}\n\n")
        response.write(f"Suggestions:\n{analysis.suggestions}")

        return response

    messages.error(request, _('File not found.'))
    return redirect('documents:document_detail', doc_id=document.id)