from celery import shared_task
import os
import boto3
from django.conf import settings
from django.core.files.base import ContentFile
from botocore.exceptions import NoCredentialsError
from .models import RfpDocument, ImprovedRfpDocument
from .rfp_processor import (
    generate_rfp_with_validation, build_vector_store,
    improved_rfp_with_validation,
    extract_text_from_pdf, is_valid_rfp_document,
    validate_rfp_inputs, improve_rfp_with_extracted_text
)

# Configure S3 client only if S3 is enabled
if settings.USE_S3:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
else:
    s3_client = None


def upload_to_s3(file_path, s3_key):
    """Upload a file to S3 bucket if S3 is enabled"""
    if not settings.USE_S3 or not s3_client:
        return None

    try:
        s3_client.upload_file(
            file_path,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key
        )
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    except NoCredentialsError:
        print("S3 credentials not available")
        return None


@shared_task
def generate_rfp_task(
        competition_name,
        competition_objectives,
        competition_description,
        government_entity,
        cost_value,
        cost_method,
        start_stage,
        end_stage,
        technical_docs,
        alternative_offers,
        initial_guarantee,
        pause_period,
        penalties,
        execution_city,
        execution_district,
        execution_region,
        required_materials,
        scope_summary,
        special_terms,
        rfp_id
):
    """
    Background task to generate RFP document with all the new parameters
    """
    try:
        # Update status to processing
        rfp = RfpDocument.objects.get(id=rfp_id)
        rfp.status = 'processing'
        rfp.save()

        # Validate inputs before proceeding
        input_data = {
            'competition_name': competition_name,
            'competition_objectives': competition_objectives,
            'competition_description': competition_description,
            'government_entity': government_entity,
            'cost_value': cost_value,
            'cost_method': cost_method,
            'start_stage': start_stage,
            'end_stage': end_stage,
            'technical_docs': technical_docs,
            'alternative_offers': alternative_offers,
            'initial_guarantee': initial_guarantee,
            'pause_period': pause_period,
            'penalties': penalties,
            'execution_city': execution_city,
            'execution_district': execution_district,
            'execution_region': execution_region,
            'required_materials': required_materials,
            'scope_summary': scope_summary,
            'special_terms': special_terms
        }

        is_valid, validation_message = validate_rfp_inputs(input_data)
        if not is_valid:
            rfp.status = 'error'
            rfp.error_message = f"Input validation failed: {validation_message}"
            rfp.save()
            return {"status": "error", "message": validation_message}

        # Generate RFP document to the temporary directory using the validation wrapper
        filename = generate_rfp_with_validation(
            competition_name,
            competition_objectives,
            competition_description,
            government_entity,
            cost_value,
            cost_method,
            start_stage,
            end_stage,
            technical_docs,
            alternative_offers,
            initial_guarantee,
            pause_period,
            penalties,
            execution_city,
            execution_district,
            execution_region,
            required_materials,
            scope_summary,
            special_terms,
            settings.TEMP_RFP_DIR,  # Use the temporary directory
            settings.STATIC_ROOT
        )

        if not filename:
            rfp.status = 'error'
            rfp.error_message = "Failed to generate RFP document. Check input parameters."
            rfp.save()
            return {"status": "error", "message": "Document generation failed"}

        # File path of the generated document
        file_path = os.path.join(settings.TEMP_RFP_DIR, filename)

        # Save file to the model (will use S3 storage backend automatically)
        with open(file_path, 'rb') as f:
            rfp.document_file.save(filename, ContentFile(f.read()), save=True)

        # Update status
        rfp.status = 'completed'
        rfp.save()

        # Cleanup temporary file
        if settings.CLEANUP_LOCAL_FILES and os.path.exists(file_path):
            os.remove(file_path)

        return {"status": "success", "document_id": rfp.id, "filename": filename}

    except Exception as e:
        # Update document status to error
        try:
            rfp = RfpDocument.objects.get(id=rfp_id)
            rfp.status = 'error'
            rfp.error_message = str(e)
            rfp.save()
        except:
            pass

        raise Exception(f"Error generating RFP: {str(e)}")


@shared_task
def improve_rfp_task(
        competition_name, competition_objectives, competition_description,
        government_entity, cost_value, cost_method, start_stage, end_stage,
        technical_docs, alternative_offers, initial_guarantee, pause_period,
        penalties, execution_city, execution_district, execution_region,
        required_materials, scope_summary, special_terms, rfp_improve_id,
        bypass_validation=False, debug_mode=False
):
    """
    Background task to improve RFP document - validation removed
    """
    try:
        # Print diagnostic info at the start
        print(f"Starting improve_rfp_task for ID: {rfp_improve_id}")

        # Update status to processing
        improved_rfp = ImprovedRfpDocument.objects.get(id=rfp_improve_id)
        improved_rfp.status = 'processing'
        improved_rfp.save()

        # Access the original document from the model
        if not improved_rfp.original_document:
            improved_rfp.status = 'error'
            improved_rfp.error_message = "Original document not found in the record"
            improved_rfp.save()
            return {"status": "error", "message": "Original document not found"}

        # Save the original document to a temporary file for processing
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        original_filename = os.path.basename(improved_rfp.original_document.name)
        temp_original_path = os.path.join(temp_dir, f"temp_{original_filename}")

        # Copy file from storage to local temp file
        with improved_rfp.original_document.open('rb') as src_file:
            with open(temp_original_path, 'wb') as dest_file:
                dest_file.write(src_file.read())

        print(f"Saved original document to temporary path: {temp_original_path}")

        # Define output path in temp directory
        output_path = os.path.join(settings.TEMP_IMPROVED_DIR, f"improved_{original_filename}")

        # Make sure output path ends with .docx
        if not output_path.endswith('.docx'):
            output_path = output_path.replace('.pdf', '.docx')

        # Build vector store
        knowledge_dir = os.path.join(settings.STATIC_ROOT, "knowledge")
        vector_store = build_vector_store(knowledge_dir)

        # Run the improvement process without validation
        print(f"Starting RFP improvement process")
        improved_filename = improve_rfp_with_extracted_text(
            temp_original_path,
            competition_name,
            competition_objectives,
            competition_description,
            output_path,
            vector_store,
            government_entity=government_entity,
            cost_value=cost_value,
            cost_method=cost_method,
            start_stage=start_stage,
            end_stage=end_stage,
            technical_docs=technical_docs,
            alternative_offers=alternative_offers,
            initial_guarantee=initial_guarantee,
            pause_period=pause_period,
            penalties=penalties,
            execution_city=execution_city,
            execution_district=execution_district,
            execution_region=execution_region,
            required_materials=required_materials,
            scope_summary=scope_summary,
            special_terms=special_terms
        )

        if not improved_filename:
            improved_rfp.status = 'error'
            improved_rfp.error_message = "Failed to improve RFP document. Check input parameters or original document."
            improved_rfp.save()

            # Cleanup temporary files
            if os.path.exists(temp_original_path):
                os.remove(temp_original_path)

            return {"status": "error", "message": "Document improvement failed"}

        # Save improved file to the model (will use S3 storage backend automatically)
        print(f"Saving improved document to model")
        with open(output_path, 'rb') as f:
            improved_rfp.improved_document.save(improved_filename, ContentFile(f.read()), save=True)

        # Update status
        improved_rfp.status = 'completed'
        improved_rfp.save()

        # Cleanup temporary files
        if settings.CLEANUP_LOCAL_FILES:
            if os.path.exists(temp_original_path):
                os.remove(temp_original_path)
            if os.path.exists(output_path):
                os.remove(output_path)

        print(f"Task completed successfully")
        return {"status": "success", "document_id": improved_rfp.id, "filename": improved_filename}

    except Exception as e:
        # Update document status to error
        try:
            print(f"Error in task: {str(e)}")
            import traceback
            print(traceback.format_exc())

            improved_rfp = ImprovedRfpDocument.objects.get(id=rfp_improve_id)
            improved_rfp.status = 'error'
            improved_rfp.error_message = str(e)
            improved_rfp.save()
        except Exception as inner_e:
            print(f"Error updating document status: {str(inner_e)}")

        # Cleanup temporary files on error
        if 'temp_original_path' in locals() and os.path.exists(temp_original_path):
            os.remove(temp_original_path)

        raise Exception(f"Error improving RFP: {str(e)}")