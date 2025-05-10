import os
import mimetypes
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile
from .models import RfpDocument, ImprovedRfpDocument
from .rfp_processor import generate_rfp_document, build_vector_store, \
    improve_rfp_with_extracted_text, read_pdf_with_fitz
import concurrent.futures

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

            # Redirect to success view instead of rendering directly
            return redirect('generator:success', rfp_id=rfp.id)

        except Exception as e:
            messages.warning(request, f'حدث خطأ أثناء إنشاء الكراسة: {str(e)}')
            return redirect('generator:rfp_form')

    # If not POST, redirect to form
    return redirect('generator:rfp_form')


def download_file(request, filename):
    """
    Download the generated RFP document.
    """
    # First check if we can find the file directly by name
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    # If file doesn't exist at direct path, try to find it through the model
    if not os.path.exists(file_path):
        try:
            # Try to find the document in the database
            rfp = RfpDocument.objects.get(document_file__endswith=filename)
            file_path = rfp.document_file.path  # Use Django's path resolution
        except (RfpDocument.DoesNotExist, RfpDocument.MultipleObjectsReturned):
            # If we can't find the document, show an error
            messages.warning(request, 'الملف المطلوب غير موجود.')
            return redirect('generator:rfp_form')

    # Now we should have the correct file_path
    if os.path.exists(file_path):
        # Use FileResponse which is better for serving files
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
        return response

    messages.warning(request, 'الملف المطلوب غير موجود.')
    return redirect('generator:rfp_form')

# Add this to your views.py
def success_view(request, rfp_id):
    """
    Display success page after RFP generation.
    """
    try:
        rfp = RfpDocument.objects.get(id=rfp_id)
        filename = os.path.basename(rfp.document_file.name)
        return render(request, 'generator/sucess.html', {
            'rfp': rfp,
            'filename': filename
        })
    except RfpDocument.DoesNotExist:
        messages.warning(request, 'المستند المطلوب غير موجود.')
        return redirect('generator:rfp_form')


def improve_rfp_form(request):
    """
    Display the RFP improvement form.
    """
    return render(request, 'generator/improve_form.html')


def improve_rfp(request):
    """
    Process form submission and improve the RFP document with optimized parallel processing.
    """
    if request.method == 'POST' and request.FILES.get('original_document'):
        # Get form data
        competition_name = request.POST.get('competition_name', '')
        competition_objectives = request.POST.get('competition_objectives', '')
        competition_description = request.POST.get('competition_description', '')
        original_document = request.FILES['original_document']

        # Validate input
        if not competition_name or not competition_objectives or not competition_description:
            messages.warning(request, 'جميع الحقول مطلوبة، يرجى التأكد من تعبئتها.')
            return redirect('generator:improve_rfp_form')

        try:
            # Save original document temporarily
            temp_original_path = os.path.join(settings.MEDIA_ROOT, 'temp', original_document.name)
            os.makedirs(os.path.dirname(temp_original_path), exist_ok=True)

            with open(temp_original_path, 'wb+') as destination:
                for chunk in original_document.chunks():
                    destination.write(chunk)

            # Output path for improved document
            output_path = os.path.join(settings.MEDIA_ROOT, 'improved_rfps', f"improved_{original_document.name}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Make sure output path ends with .docx
            if not output_path.endswith('.docx'):
                output_path = output_path.replace('.pdf', '.docx')

            # Run concurrent tasks for PDF extraction and vector store building
            print("🔹 Starting parallel initialization tasks...")

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Define the tasks
                knowledge_dir = os.path.join(settings.STATIC_ROOT, "knowledge")
                vector_store_future = executor.submit(build_vector_store, knowledge_dir)
                pdf_text_future = executor.submit(read_pdf_with_fitz, temp_original_path)

                # Get results as they complete
                vector_store = vector_store_future.result()
                pdf_text = pdf_text_future.result()

                print("✅ Completed parallel initialization")

            # Run the optimization function with pre-extracted text
            improved_filename = improve_rfp_with_extracted_text(
                pdf_text,
                competition_name,
                competition_objectives,
                competition_description,
                output_path,
                vector_store
            )

            # Create improved RFP document record
            improved_rfp = ImprovedRfpDocument(
                competition_name=competition_name,
                competition_objectives=competition_objectives,
                competition_description=competition_description
            )

            # Save original file to the model
            improved_rfp.original_document.save(original_document.name, original_document)

            # Save improved file to the model
            with open(output_path, 'rb') as f:
                improved_rfp.improved_document.save(improved_filename, ContentFile(f.read()))

            improved_rfp.save()

            # Cleanup temporary files
            if os.path.exists(temp_original_path):
                os.remove(temp_original_path)

            # Return success view
            return redirect('generator:improve_success', rfp_id=improved_rfp.id)

        except Exception as e:
            # Enhanced error logging
            import traceback
            error_details = traceback.format_exc()
            print(f"Error during RFP improvement: {error_details}")
            messages.warning(request, f'حدث خطأ أثناء تحسين الكراسة: {str(e)}')
            return redirect('generator:improve_rfp_form')

    # If not POST or no file, redirect to form
    return redirect('generator:improve_rfp_form')
def improve_success_view(request, rfp_id):
    """
    Display success page after RFP improvement.
    """
    try:
        rfp = ImprovedRfpDocument.objects.get(id=rfp_id)
        filename = os.path.basename(rfp.improved_document.name)
        return render(request, 'generator/improve_success.html', {
            'rfp': rfp,
            'filename': filename
        })
    except ImprovedRfpDocument.DoesNotExist:
        messages.warning(request, 'المستند المطلوب غير موجود.')
        return redirect('generator:improve_rfp_form')


def download_improved_file(request, filename):
    """
    Download the improved RFP document.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, 'improved_rfps', filename)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            mime_type, _ = mimetypes.guess_type(file_path)
            response = FileResponse(
                fh,
                as_attachment=True,
                filename=filename
            )
            return response

    messages.warning(request, 'الملف المطلوب غير موجود.')
    return redirect('generator:improve_rfp_form')