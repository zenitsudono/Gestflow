from django.db import models
from django.contrib.auth import get_user_model
import uuid
import mimetypes
from apps.resources.models import Resource

User = get_user_model()

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='resources/documents/')
    file_type = models.CharField(max_length=100, blank=True, null=True)
    size = models.IntegerField(help_text="File size in bytes", blank=True, null=True)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        if self.file:
            if not self.size:
                try:
                    self.size = self.file.size
                except Exception:
                    pass
            if not self.file_type:
                mime, _ = mimetypes.guess_type(self.file.name)
                self.file_type = mime or 'application/octet-stream'
        super().save(*args, **kwargs)
