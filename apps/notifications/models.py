from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Notification(models.Model):
    TYPE_CHOICES = (
        ('email', 'Email'),
        ('in-app', 'In-App'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='in-app')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.email} - {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def send(self):
        if self.type == 'email':
            from .tasks import send_notification_email
            send_notification_email.delay(str(self.id))
        # In-app notifications are already persisted and readable by client.
