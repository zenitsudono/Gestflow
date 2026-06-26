from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, ARCHIVE, RESTORE
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255)
    changes = models.JSONField(default=dict, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor = self.user.email if self.user else 'System'
        return f"{self.model_name} ({self.object_id}) - {self.action} by {actor} at {self.timestamp}"
