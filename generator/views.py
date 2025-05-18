import os
import mimetypes
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse
from .models import RfpDocument, ImprovedRfpDocument
from .tasks import generate_rfp_task, improve_rfp_task
from celery.result import AsyncResult
from .rfp_processor import validate_rfp_inputs, extract_text_from_pdf, is_valid_rfp_document


def rfp_form(request):
    """
    Display the RFP generator form.
    """
    return render(request, 'generator/index.html')


def generate_rfp(request):
    """
    Process form submission and queue RFP generation as a background task.
    """
    if request.method == 'POST':
        # Collect all fields from the form
        field_names = [
            'competition_name', 'competition_objectives', 'competition_description',
            'government_entity', 'cost_value', 'cost_method', 'start_stage', 'end_stage',
            'technical_docs', 'alternative_offers', 'initial_guarantee', 'pause_period',
            'penalties', 'execution_city', 'execution_district', 'execution_region',
            'required_materials', 'special_terms'
        ]

        # Get all form data
        data = {field: request.POST.get(field, '').strip() for field in field_names}

        # Create a summary of the scope from the provided data
        scope_summary = f"""
اسم المشروع: {data['competition_name']}
الجهة الحكومية: {data['government_entity']}
وصف المنافسة: {data['competition_description']}
المدينة: {data['execution_city']}, الحي: {data['execution_district']}, المنطقة: {data['execution_region']}
أهداف المشروع: {data['competition_objectives']}
"""

        # Validate required fields
        required_fields = ['competition_name', 'competition_objectives', 'competition_description', 'government_entity']
        missing_fields = [field for field in required_fields if not data[field]]
        if missing_fields:
            messages.warning(request, f'الحقول التالية مطلوبة: {", ".join(missing_fields)}')
            return redirect('generator:rfp_form')

        # AI validation of input quality
        inputs_valid, validation_reason = validate_rfp_inputs(data)
        if not inputs_valid:
            messages.warning(request, f'تحليل الذكاء الاصطناعي: {validation_reason}')
            return redirect('generator:rfp_form')

        try:
            # Create RFP document record with pending status
            rfp = RfpDocument(
                competition_name=data['competition_name'],
                competition_objectives=data['competition_objectives'],
                competition_description=data['competition_description'],
                status='pending'
            )
            rfp.save()

            # Queue the task in Celery with all parameters
            task = generate_rfp_task.delay(
                data['competition_name'],
                data['competition_objectives'],
                data['competition_description'],
                data['government_entity'],
                data['cost_value'],
                data['cost_method'],
                data['start_stage'],
                data['end_stage'],
                data['technical_docs'],
                data['alternative_offers'],
                data['initial_guarantee'],
                data['pause_period'],
                data['penalties'],
                data['execution_city'],
                data['execution_district'],
                data['execution_region'],
                data['required_materials'],
                scope_summary,
                data['special_terms'],
                rfp.id
            )

            # Save task ID for status tracking
            rfp.task_id = task.id
            rfp.save()

            # Redirect to waiting page
            return redirect('generator:task_status', task_id=task.id, document_type='rfp', document_id=rfp.id)

        except Exception as e:
            # Enhanced error logging
            import traceback
            error_details = traceback.format_exc()
            print(f"Error during RFP generation: {error_details}")
            messages.warning(request, f'حدث خطأ أثناء إنشاء الكراسة: {str(e)}')
            return redirect('generator:rfp_form')

    # If not POST, redirect to form
    return redirect('generator:rfp_form')

def improve_rfp(request):
    """
    Process form submission and queue RFP improvement as a background task.
    Validations removed.
    """
    print("Improve RFP form submitted")
    if request.method == 'POST' and request.FILES.get('original_document'):
        # Collect all fields from the form
        field_names = [
            'competition_name', 'competition_objectives', 'competition_description',
            'government_entity', 'cost_value', 'cost_method', 'start_stage', 'end_stage',
            'technical_docs', 'alternative_offers', 'initial_guarantee', 'pause_period',
            'penalties', 'execution_city', 'execution_district', 'execution_region',
            'required_materials', 'special_terms'
        ]

        # Get all form data
        data = {field: request.POST.get(field, '').strip() for field in field_names}
        print(f"Form data collected: {len(data)} fields")

        # Get the uploaded file
        original_document = request.FILES['original_document']
        print(f"Uploaded file: {original_document.name}")

        # Create a summary of the scope from the provided data
        scope_summary = f"""
اسم المشروع: {data['competition_name']}
الجهة الحكومية: {data['government_entity']}
وصف المنافسة: {data['competition_description']}
المدينة: {data['execution_city']}, الحي: {data['execution_district']}, المنطقة: {data['execution_region']}
أهداف المشروع: {data['competition_objectives']}
"""

        try:
            # Create temp directories if they don't exist
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            # Create improved RFP document record with pending status
            print("Creating ImprovedRfpDocument record")
            improved_rfp = ImprovedRfpDocument(
                competition_name=data['competition_name'],
                competition_objectives=data['competition_objectives'],
                competition_description=data['competition_description'],
                status='pending'
            )

            # Save original file to the model
            print("Saving original file to model")
            improved_rfp.original_document.save(original_document.name, original_document)
            improved_rfp.save()
            print(f"Record created with ID: {improved_rfp.id}")

            # Queue the task in Celery with all parameters
            print("Queueing Celery task")
            task = improve_rfp_task.delay(
                data['competition_name'],
                data['competition_objectives'],
                data['competition_description'],
                data['government_entity'],
                data['cost_value'],
                data['cost_method'],
                data['start_stage'],
                data['end_stage'],
                data['technical_docs'],
                data['alternative_offers'],
                data['initial_guarantee'],
                data['pause_period'],
                data['penalties'],
                data['execution_city'],
                data['execution_district'],
                data['execution_region'],
                data['required_materials'],
                scope_summary,
                data['special_terms'],
                improved_rfp.id
            )

            # Save task ID for status tracking
            improved_rfp.task_id = task.id
            improved_rfp.save()
            print(f"Task ID saved: {task.id}")

            # Redirect to waiting page
            redirect_url = reverse('generator:task_status', kwargs={
                'task_id': task.id,
                'document_type': 'improve',
                'document_id': improved_rfp.id
            })
            print(f"Redirecting to: {redirect_url}")
            return redirect(redirect_url)

        except Exception as e:
            # Enhanced error logging
            import traceback
            error_details = traceback.format_exc()
            print(f"Error during RFP improvement: {error_details}")

            messages.warning(request, f'حدث خطأ أثناء تحسين الكراسة: {str(e)}')
            return redirect('generator:improve_rfp_form')

    # If not POST or no file, redirect to form
    return redirect('generator:improve_rfp_form')

def improve_rfp_form(request):
    """
    Display the RFP improvement form.
    """
    return render(request, 'generator/improve_form.html')


def task_status(request, task_id, document_type, document_id):
    """
    Display a waiting page that checks task status via AJAX.
    """
    context = {
        'task_id': task_id,
        'document_type': document_type,
        'document_id': document_id
    }
    return render(request, 'generator/task_status.html', context)


def check_task_status(request, task_id, document_type, document_id):
    """
    AJAX endpoint to check task status.
    """
    result = AsyncResult(task_id)

    if document_type == 'rfp':
        try:
            rfp = RfpDocument.objects.get(id=document_id)
            status = rfp.status
        except RfpDocument.DoesNotExist:
            status = 'error'
    else:  # improve
        try:
            rfp = ImprovedRfpDocument.objects.get(id=document_id)
            status = rfp.status
        except ImprovedRfpDocument.DoesNotExist:
            status = 'error'

    if status == 'completed':
        if document_type == 'rfp':
            return JsonResponse({
                'status': 'completed',
                'redirect_url': reverse('generator:success', args=[document_id])
            })
        else:  # improve
            return JsonResponse({
                'status': 'completed',
                'redirect_url': reverse('generator:improve_success', args=[document_id])
            })
    elif status == 'error':
        error_message = "حدث خطأ أثناء معالجة الطلب"
        if document_type == 'rfp':
            try:
                error_message = rfp.error_message or error_message
            except:
                pass
        else:
            try:
                error_message = rfp.error_message or error_message
            except:
                pass

        return JsonResponse({
            'status': 'error',
            'error': error_message
        })
    else:
        return JsonResponse({
            'status': 'processing'
        })


def success_view(request, rfp_id):
    """
    Display success page after RFP generation.
    """
    try:
        rfp = RfpDocument.objects.get(id=rfp_id)

        # Check if task is completed
        if rfp.status != 'completed':
            return redirect('generator:task_status', task_id=rfp.task_id, document_type='rfp', document_id=rfp.id)

        filename = os.path.basename(rfp.document_file.name)
        return render(request, 'generator/success.html', {
            'rfp': rfp,
            'filename': filename
        })
    except RfpDocument.DoesNotExist:
        messages.warning(request, 'المستند المطلوب غير موجود.')
        return redirect('generator:rfp_form')


def improve_success_view(request, rfp_id):
    """
    Display success page after RFP improvement.
    """
    try:
        rfp = ImprovedRfpDocument.objects.get(id=rfp_id)

        # Check if task is completed
        if rfp.status != 'completed':
            return redirect('generator:task_status', task_id=rfp.task_id, document_type='improve', document_id=rfp.id)

        filename = os.path.basename(rfp.improved_document.name)
        return render(request, 'generator/improve_success.html', {
            'rfp': rfp,
            'filename': filename
        })
    except ImprovedRfpDocument.DoesNotExist:
        messages.warning(request, 'المستند المطلوب غير موجود.')
        return redirect('generator:improve_rfp_form')


def download_by_id(request, rfp_id):
    """
    Download RFP document by ID instead of filename.
    More reliable, especially with non-ASCII filenames.
    """
    try:
        rfp = RfpDocument.objects.get(id=rfp_id)
        if not rfp.document_file:
            messages.warning(request, 'الملف غير موجود مع هذا السجل.')
            return redirect('generator:rfp_form')

        if settings.USE_S3:
            return redirect(rfp.document_file.url)
        else:
            return FileResponse(
                rfp.document_file.open('rb'),
                as_attachment=True,
                filename=os.path.basename(rfp.document_file.name)
            )
    except RfpDocument.DoesNotExist:
        messages.warning(request, 'السجل المطلوب غير موجود.')
        return redirect('generator:rfp_form')


def download_file(request, filename):
    """
    Download the generated RFP document.
    Enhanced to better handle Arabic filenames with S3.
    """
    print(f"Attempting to download: {filename}")  # Debug logging

    if settings.USE_S3:
        try:
            # Try different query approaches to find the document
            # Method 1: Filter containing the filename without path
            rfp = RfpDocument.objects.filter(
                document_file__contains=filename.split('/')[-1]
            ).first()

            if not rfp:
                # Method 2: Try by endswith with relaxed constraints
                rfp = RfpDocument.objects.filter(
                    document_file__endswith='_rfp.docx'
                ).order_by('-id').first()

            if rfp:
                print(f"Found document: {rfp.document_file.name}")
                return redirect(rfp.document_file.url)
            else:
                messages.warning(request, 'الملف المطلوب غير موجود.')
                return redirect('generator:rfp_form')

        except Exception as e:
            print(f"Error accessing file: {str(e)}")
            messages.warning(request, f'حدث خطأ أثناء الوصول للملف: {str(e)}')
            return redirect('generator:rfp_form')
    else:
        # Local storage code (unchanged)
        file_path = os.path.join(settings.MEDIA_ROOT, 'rfp_documents', filename)

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
            # Check file size to ensure it's not empty
            if os.path.getsize(file_path) == 0:
                messages.warning(request, 'الملف المطلوب فارغ.')
                return redirect('generator:rfp_form')

            # Use FileResponse which is better for serving files
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path)
            )
            return response

        messages.warning(request, 'الملف المطلوب غير موجود.')
        return redirect('generator:rfp_form')


def download_improved_by_id(request, rfp_id):
    """
    Download improved RFP document by ID instead of filename.
    More reliable, especially with non-ASCII filenames.
    """
    try:
        rfp = ImprovedRfpDocument.objects.get(id=rfp_id)
        if not rfp.improved_document:
            messages.warning(request, 'الملف غير موجود مع هذا السجل.')
            return redirect('generator:improve_rfp_form')

        if settings.USE_S3:
            return redirect(rfp.improved_document.url)
        else:
            return FileResponse(
                rfp.improved_document.open('rb'),
                as_attachment=True,
                filename=os.path.basename(rfp.improved_document.name)
            )
    except ImprovedRfpDocument.DoesNotExist:
        messages.warning(request, 'السجل المطلوب غير موجود.')
        return redirect('generator:improve_rfp_form')


def download_improved_file(request, filename):
    """
    Download the improved RFP document.
    Enhanced to better handle Arabic filenames with S3.
    """
    print(f"Attempting to download improved: {filename}")  # Debug logging

    if settings.USE_S3:
        try:
            # Try different query approaches to find the document
            # Method 1: Filter containing the filename without path
            rfp = ImprovedRfpDocument.objects.filter(
                improved_document__contains=filename.split('/')[-1]
            ).first()

            if not rfp:
                # Method 2: Try by endswith with relaxed constraints for improved files
                rfp = ImprovedRfpDocument.objects.filter(
                    improved_document__endswith='.docx'
                ).order_by('-id').first()

            if rfp:
                print(f"Found improved document: {rfp.improved_document.name}")
                return redirect(rfp.improved_document.url)
            else:
                messages.warning(request, 'الملف المطلوب غير موجود.')
                return redirect('generator:improve_rfp_form')

        except Exception as e:
            print(f"Error accessing improved file: {str(e)}")
            messages.warning(request, f'حدث خطأ أثناء الوصول للملف: {str(e)}')
            return redirect('generator:improve_rfp_form')
    else:
        # For local storage
        file_path = os.path.join(settings.MEDIA_ROOT, 'improved_rfps', filename)

        # If file doesn't exist at direct path, try to find it through the model
        if not os.path.exists(file_path):
            try:
                # Try to find the document in the database
                rfp = ImprovedRfpDocument.objects.get(improved_document__endswith=filename)
                file_path = rfp.improved_document.path  # Use Django's path resolution
            except (ImprovedRfpDocument.DoesNotExist, ImprovedRfpDocument.MultipleObjectsReturned):
                # If we can't find the document, show an error
                messages.warning(request, 'الملف المطلوب غير موجود.')
                return redirect('generator:improve_rfp_form')

        # Now we should have the correct file_path
        if os.path.exists(file_path):
            # Check file size to ensure it's not empty
            if os.path.getsize(file_path) == 0:
                messages.warning(request, 'الملف المطلوب فارغ.')
                return redirect('generator:improve_rfp_form')

            # Use FileResponse which is better for serving files
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