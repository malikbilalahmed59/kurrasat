from django.db import models
from django.utils import timezone

class RfpDocument(models.Model):
    competition_name = models.CharField(max_length=255)
    competition_description = models.TextField()
    competition_objectives = models.TextField()
    document_file = models.FileField(upload_to='rfp_documents/')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.competition_name


class ImprovedRfpDocument(models.Model):
    original_document = models.FileField(upload_to='original_rfps/')
    improved_document = models.FileField(upload_to='improved_rfps/')
    competition_name = models.CharField(max_length=255)
    competition_objectives = models.TextField()
    competition_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.competition_name