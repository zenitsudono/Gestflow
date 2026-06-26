import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from apps.accounts.models import CustomUser, Role
from apps.resources.models import Resource, Category
from apps.documents.models import Document
from apps.notifications.models import Notification
from tests.conftest import UserFactory, CategoryFactory, ResourceFactory

@pytest.mark.django_db
def test_category_api(api_client, db_roles):
    admin = UserFactory(role=db_roles['admin'])
    url = reverse('category-list')
    
    api_client.force_authenticate(user=admin)
    
    # Test Create
    response = api_client.post(url, {'name': 'New Category', 'description': 'Description'})
    assert response.status_code == status.HTTP_201_CREATED
    assert Category.objects.filter(name='New Category').exists()

    # Test List
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

@pytest.mark.django_db
def test_resource_api_actions(api_client, db_roles):
    user = UserFactory(role=db_roles['user'], department='it')
    category = CategoryFactory()
    resource = ResourceFactory(category=category, owner=user, department='it')
    
    api_client.force_authenticate(user=user)
    
    # Test Archive
    archive_url = reverse('resource-archive', args=[resource.id])
    response = api_client.post(archive_url)
    assert response.status_code == status.HTTP_200_OK
    resource.refresh_from_db()
    assert resource.is_archived is True

    # Test Restore
    restore_url = reverse('resource-restore', args=[resource.id])
    response = api_client.post(restore_url)
    assert response.status_code == status.HTTP_200_OK
    resource.refresh_from_db()
    assert resource.is_archived is False

    # Test History
    history_url = reverse('resource-history', args=[resource.id])
    response = api_client.get(history_url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0

    # Test Statistics
    stats_url = reverse('resource-statistics')
    response = api_client.get(stats_url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['total'] == 1

@pytest.mark.django_db
def test_document_api_flow(api_client, db_roles):
    user = UserFactory(role=db_roles['user'], department='it')
    resource = ResourceFactory(owner=user, department='it')
    
    api_client.force_authenticate(user=user)
    
    url = reverse('document-list')
    
    # Create mock file
    mock_file = SimpleUploadedFile("test_doc.pdf", b"pdf content", content_type="application/pdf")
    
    # Test upload
    response = api_client.post(url, {
        'file': mock_file,
        'resource': resource.id
    }, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert Document.objects.filter(resource=resource).exists()
    doc = Document.objects.first()
    
    # Test preview
    preview_url = reverse('document-preview', args=[doc.id])
    response = api_client.get(preview_url)
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == "application/pdf"

@pytest.mark.django_db
def test_notification_api(api_client, db_roles):
    user = UserFactory(role=db_roles['user'])
    notification = Notification.objects.create(
        recipient=user,
        title="Test In-App",
        message="Message content",
        type='in-app'
    )
    
    api_client.force_authenticate(user=user)
    
    # Test List
    url = reverse('notification-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    
    # Test Mark as read
    read_url = reverse('notification-read', args=[notification.id])
    response = api_client.post(read_url)
    assert response.status_code == status.HTTP_200_OK
    notification.refresh_from_db()
    assert notification.is_read is True

@pytest.mark.django_db
def test_ssr_web_views(api_client, db_roles):
    admin = UserFactory(role=db_roles['admin'], department='it')
    regular_user = UserFactory(role=db_roles['user'], department='it')
    
    # 1. Test Login View GET
    login_url = reverse('login')
    response = api_client.get(login_url)
    assert response.status_code == 200
    assert b"Sign in to GestiFlow" in response.content or b"Welcome to GestiFlow" in response.content

    # 2. Test Login View POST (Authentication)
    response = api_client.post(login_url, {
        'email': regular_user.email,
        'password': 'testpassword'  # Note: UserFactory password defaults to something, we can mock authentication or authenticate
    })
    # Since UserFactory doesn't set a default raw password checked by authenticate(), we can manually set it:
    regular_user.set_password("secret_pass")
    regular_user.save()
    
    response = api_client.post(login_url, {
        'email': regular_user.email,
        'password': 'secret_pass'
    })
    assert response.status_code == 302  # Redirects to dashboard
    
    # 3. Test Dashboard View
    dashboard_url = reverse('dashboard')
    api_client.force_login(user=regular_user)
    response = api_client.get(dashboard_url)
    assert response.status_code == 200
    
    # 4. Test Settings View GET & POST
    settings_url = reverse('settings')
    response = api_client.get(settings_url)
    assert response.status_code == 200
    
    response = api_client.post(settings_url, {
        'first_name': 'UpdatedFirst',
        'last_name': 'UpdatedLast',
        'phone': '123456',
        'bio': 'New bio info'
    })
    assert response.status_code == 302  # Redirects back to settings
    regular_user.refresh_from_db()
    assert regular_user.first_name == "UpdatedFirst"
    assert regular_user.phone == "123456"

    # 5. Test User Management (Admin only)
    users_url = reverse('user_management')
    
    # Regular user gets 404
    api_client.force_login(user=regular_user)
    response = api_client.get(users_url)
    assert response.status_code == 404
    
    # Admin user gets 200
    api_client.force_login(user=admin)
    response = api_client.get(users_url)
    assert response.status_code == 200
    
    # Admin POST update user role
    role_manager = db_roles['manager']
    response = api_client.post(users_url, {
        'action_type': 'update_role',
        'user_id': regular_user.id,
        'role': role_manager.id,
        'department': 'hr'
    })
    assert response.status_code == 302
    regular_user.refresh_from_db()
    assert regular_user.role == role_manager
    assert regular_user.department == 'hr'


@pytest.mark.django_db
def test_resource_web_views_permissions(api_client, db_roles):
    # 1. Unauthenticated redirects to login
    list_url = reverse('resource_list')
    response = api_client.get(list_url)
    assert response.status_code == 302
    assert 'login' in response.url

    # 2. Authenticated but no role redirects to login
    user_no_role = UserFactory(role=None)
    api_client.force_login(user=user_no_role)
    response = api_client.get(list_url)
    assert response.status_code == 302
    assert 'login' in response.url

    # Setup roles, departments, users
    admin = UserFactory(role=db_roles['admin'], department='it')
    manager_it = UserFactory(role=db_roles['manager'], department='it')
    manager_hr = UserFactory(role=db_roles['manager'], department='hr')
    user_it_1 = UserFactory(role=db_roles['user'], department='it')
    user_it_2 = UserFactory(role=db_roles['user'], department='it')

    # Create resources
    res_it_1 = ResourceFactory(owner=user_it_1, department='it')
    res_it_2 = ResourceFactory(owner=user_it_2, department='it')
    res_hr = ResourceFactory(owner=manager_hr, department='hr')

    # 3. Admin user list access -> Sees all resources
    api_client.force_login(user=admin)
    response = api_client.get(list_url)
    assert response.status_code == 200
    resources = list(response.context['resources'])
    assert res_it_1 in resources
    assert res_it_2 in resources
    assert res_hr in resources

    # Admin detail access
    detail_url_it_1 = reverse('resource_detail', args=[res_it_1.id])
    response = api_client.get(detail_url_it_1)
    assert response.status_code == 200
    assert response.context['resource'] == res_it_1

    # 4. Manager (IT) list access -> Sees only IT resources
    api_client.force_login(user=manager_it)
    response = api_client.get(list_url)
    assert response.status_code == 200
    resources = list(response.context['resources'])
    assert res_it_1 in resources
    assert res_it_2 in resources
    assert res_hr not in resources

    # Manager (IT) detail access to IT resource -> 200
    response = api_client.get(detail_url_it_1)
    assert response.status_code == 200

    # Manager (IT) detail access to HR resource -> Redirects to resource_list
    detail_url_hr = reverse('resource_detail', args=[res_hr.id])
    response = api_client.get(detail_url_hr)
    assert response.status_code == 302
    assert response.url == list_url

    # 5. User (IT 1) list access -> Sees only their own resource
    api_client.force_login(user=user_it_1)
    response = api_client.get(list_url)
    assert response.status_code == 200
    resources = list(response.context['resources'])
    assert res_it_1 in resources
    assert res_it_2 not in resources
    assert res_hr not in resources

    # User (IT 1) detail access to own resource -> 200
    response = api_client.get(detail_url_it_1)
    assert response.status_code == 200

    # User (IT 1) detail access to another IT resource -> Redirects to resource_list
    detail_url_it_2 = reverse('resource_detail', args=[res_it_2.id])
    response = api_client.get(detail_url_it_2)
    assert response.status_code == 302
    assert response.url == list_url

