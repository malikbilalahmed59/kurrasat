import os
import mimetypes
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile
from .models import RfpDocument
from .rfp_processor import generate_rfp_document


def rfp_form(request):
    """
    Display the RFP generator form.
    """
    return render(request, 'generator/index.html')


def generate_rfp(request):
    """
    Process form submission and generate the RFP document.
    """
    if request.method == 'POST':
        # Get form data
        competition_name = request.POST.get('competition_name', '')
        competition_objectives = request.POST.get('competition_objectives', '')
        competition_description = request.POST.get('competition_description', '')

        # Validate input
        if not competition_name or not competition_objectives or not competition_description:
            messages.warning(request, 'جميع الحقول مطلوبة، يرجى التأكد من تعبئتها.')
            return redirect('generator:rfp_form')

        try:
            # Generate RFP document
            filename = generate_rfp_document(
                competition_name,
                competition_objectives,
                competition_description,
                settings.MEDIA_ROOT,
                settings.STATIC_ROOT
            )

            # Save document reference to database
            file_path = os.path.join(settings.MEDIA_ROOT, filename)

            # Create RFP document record
            rfp = RfpDocument(
                competition_name=competition_name,
                competition_objectives=competition_objectives,
                competition_description=competition_description
            )

            # Save file to the model
            with open(file_path, 'rb') as f:
                rfp.document_file.save(filename, ContentFile(f.read()))

            rfp.save()

            # Return success view
            return render(request, 'generator/success.html', {
                'rfp': rfp,
                'filename': filename
            })

        except Exception as e:
            messages.warning(request, f'حدث خطأ أثناء إنشاء الكراسة: {str(e)}')
            return redirect('generator:rfp_form')

    # If not POST, redirect to form
    return redirect('generator:rfp_form')


def download_file(request, filename):
    """
    Download the generated RFP document.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            mime_type, _ = mimetypes.guess_type(file_path)
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    messages.warning(request, 'الملف المطلوب غير موجود.')
    return redirect('generator:rfp_form')