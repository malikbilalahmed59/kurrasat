from django.db import models
from django.utils import timezone
from django.conf import settings

# Import storage backends conditionally
if settings.USE_S3:
    from kurrasat.storage_backends import RfpDocumentStorage, ImprovedRfpStorage, OriginalRfpStorage
else:
    RfpDocumentStorage = None
    ImprovedRfpStorage = None
    OriginalRfpStorage = None


class RfpDocument(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    )

    competition_name = models.CharField(max_length=255)
    competition_description = models.TextField()
    competition_objectives = models.TextField()

    # Use S3 storage if configured
    if settings.USE_S3:
        document_file = models.FileField(upload_to='', storage=RfpDocumentStorage())
    else:
        document_file = models.FileField(upload_to='rfp_documents/')

    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.competition_name


class ImprovedRfpDocument(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    )

    # Use S3 storage if configured
    if settings.USE_S3:
        original_document = models.FileField(upload_to='', storage=OriginalRfpStorage())
        improved_document = models.FileField(upload_to='', storage=ImprovedRfpStorage())
    else:
        original_document = models.FileField(upload_to='original_rfps/')
        improved_document = models.FileField(upload_to='improved_rfps/')

    competition_name = models.CharField(max_length=255)
    competition_objectives = models.TextField()
    competition_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.competition_name