import pytest
from django.urls import reverse
from rest_framework import status
from apps.resources.models import Resource, Category
from apps.audit.models import AuditLog
from tests.conftest import UserFactory, CategoryFactory, ResourceFactory

@pytest.mark.django_db
def test_resource_soft_delete(db_roles):
    user = UserFactory(role=db_roles['user'])
    category = CategoryFactory()
    resource = ResourceFactory(category=category, owner=user)
    
    assert resource.is_archived is False
    
    resource.archive()
    assert resource.is_archived is True
    
    resource.restore()
    assert resource.is_archived is False

@pytest.mark.django_db
def test_resource_querysets_by_role(api_client, db_roles):
    admin = UserFactory(role=db_roles['admin'])
    manager_it = UserFactory(role=db_roles['manager'], department='it')
    manager_hr = UserFactory(role=db_roles['manager'], department='hr')
    regular_user = UserFactory(role=db_roles['user'], department='it')

    # Create resources
    res_it_owner = ResourceFactory(department='it', owner=regular_user)
    res_it_other = ResourceFactory(department='it', owner=admin)
    res_hr = ResourceFactory(department='hr', owner=admin)

    url = reverse('resource-list')

    # 1. Admin should see all active resources
    api_client.force_authenticate(user=admin)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 3

    # 2. Manager IT should see resources in IT department
    api_client.force_authenticate(user=manager_it)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 2

    # 3. Manager HR should see resources in HR department
    api_client.force_authenticate(user=manager_hr)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

    # 4. User should see only resources they own
    api_client.force_authenticate(user=regular_user)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == str(res_it_owner.id)

@pytest.mark.django_db
def test_audit_signals_on_resource_crud(db_roles):
    # Setup user session mock inside thread local
    from apps.audit.middleware import _thread_locals
    user = UserFactory(role=db_roles['user'], department='it')
    _thread_locals.user = user
    _thread_locals.ip = "127.0.0.1"

    # 1. CREATE signal check
    category = CategoryFactory()
    resource = ResourceFactory(category=category, owner=user, title="Original Title", department='it')
    
    log = AuditLog.objects.filter(model_name='Resource', object_id=str(resource.id)).first()
    assert log is not None
    assert log.action == 'CREATE'
    assert log.user == user
    assert log.changes['title'] == [None, 'Original Title']

    # 2. UPDATE signal check
    resource.title = "Updated Title"
    resource.save()
    
    log = AuditLog.objects.filter(model_name='Resource', object_id=str(resource.id), action='UPDATE').first()
    assert log is not None
    assert log.changes['title'] == ['Original Title', 'Updated Title']

    # Clean up thread local
    _thread_locals.user = None
    _thread_locals.ip = None
