from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import models
from django.db.models.fields.files import FieldFile
import uuid
import datetime

from apps.resources.models import Resource, Category
from apps.accounts.models import CustomUser
from .models import AuditLog
from .middleware import get_current_user, get_current_ip

_original_states = {}

def get_serialized_value(val):
    if isinstance(val, uuid.UUID):
        return str(val)
    elif isinstance(val, models.Model):
        return str(val.pk)
    elif isinstance(val, FieldFile):
        try:
            return val.url if val and val.name else None
        except ValueError:
            return None
    elif isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    return val

@receiver(pre_save, sender=Resource)
@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=CustomUser)
def pre_save_audit(sender, instance, **kwargs):
    if instance.pk:
        try:
            db_obj = sender.objects.get(pk=instance.pk)
            state = {}
            for field in instance._meta.fields:
                if field.name == 'password':
                    continue
                val = getattr(db_obj, field.name)
                state[field.name] = get_serialized_value(val)
            _original_states[instance.pk] = state
        except sender.DoesNotExist:
            pass

@receiver(post_save, sender=Resource)
@receiver(post_save, sender=Category)
@receiver(post_save, sender=CustomUser)
def post_save_audit(sender, instance, created, **kwargs):
    user = get_current_user()
    ip = get_current_ip()
    
    action = 'CREATE' if created else 'UPDATE'
    model_name = sender.__name__
    object_id = str(instance.pk)
    
    changes = {}
    if created:
        for field in instance._meta.fields:
            if field.name == 'password':
                continue
            val = getattr(instance, field.name)
            changes[field.name] = [None, get_serialized_value(val)]
    else:
        orig_state = _original_states.pop(instance.pk, {})
        for field in instance._meta.fields:
            if field.name == 'password':
                continue
            val = getattr(instance, field.name)
            serialized_val = get_serialized_value(val)
            
            old_val = orig_state.get(field.name)
            if old_val != serialized_val:
                changes[field.name] = [old_val, serialized_val]
                
    if changes:
        if action == 'UPDATE':
            if 'is_archived' in changes:
                old_archived, new_archived = changes['is_archived']
                if not old_archived and new_archived:
                    action = 'ARCHIVE'
                elif old_archived and not new_archived:
                    action = 'RESTORE'
                    
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            changes=changes,
            ip_address=ip
        )

@receiver(post_delete, sender=Resource)
@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=CustomUser)
def post_delete_audit(sender, instance, **kwargs):
    user = get_current_user()
    ip = get_current_ip()
    
    name_val = instance.title if hasattr(instance, 'title') else (instance.email if hasattr(instance, 'email') else str(instance))
    
    AuditLog.objects.create(
        user=user,
        action='DELETE',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        changes={'deleted': [name_val, None]},
        ip_address=ip
    )
