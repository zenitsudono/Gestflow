from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catégorie de Réclamation"
        verbose_name_plural = "Catégories de Réclamations"
        ordering = ['name']

    def __str__(self):
        return self.name

class Resource(models.Model):
    STATUS_CHOICES = (
        ('active', 'En cours'),
        ('inactive', 'Résolue'),
        ('pending', 'En attente'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='resources')
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='resources')
    department = models.CharField(max_length=50, blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réclamation"
        verbose_name_plural = "Réclamations"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def archive(self):
        self.is_archived = True
        self.save()

    def restore(self):
        self.is_archived = False
        self.save()

    def get_history(self):
        from apps.audit.models import AuditLog
        return AuditLog.objects.filter(model_name='Resource', object_id=str(self.id)).order_by('-timestamp')
