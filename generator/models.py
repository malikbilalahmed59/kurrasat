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