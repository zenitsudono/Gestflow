from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.resources.models import Resource
from apps.notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(pre_save, sender=Resource)
def resource_pre_save(sender, instance, **kwargs):
    try:
        old_instance = Resource.objects.get(pk=instance.pk)
        instance._old_status = old_instance.status
    except Resource.DoesNotExist:
        instance._old_status = None

@receiver(post_save, sender=Resource)
def resource_post_save(sender, instance, created, **kwargs):
    if created:
        # 1. Notify Owner
        Notification.objects.create(
            recipient=instance.owner,
            type='in-app',
            title="Réclamation créée",
            message=f"Votre réclamation '{instance.title}' a été créée avec succès."
        )
        # 2. Notify Managers of the same department
        if instance.department:
            managers = User.objects.filter(role__name='manager', department=instance.department)
            for manager in managers:
                Notification.objects.create(
                    recipient=manager,
                    type='in-app',
                    title=f"Nouvelle réclamation - {instance.category.name}",
                    message=f"Une nouvelle réclamation '{instance.title}' a été soumise dans le département {instance.department.upper()}."
                )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            # Notify Owner
            status_display = instance.get_status_display()
            Notification.objects.create(
                recipient=instance.owner,
                type='in-app',
                title="Statut mis à jour",
                message=f"Le statut de votre réclamation '{instance.title}' a été changé en '{status_display}'."
            )
