import pytest
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import CustomUser, Role
from tests.conftest import UserFactory

@pytest.mark.django_db
def test_create_user():
    role = Role.objects.create(name=Role.USER)
    user = CustomUser.objects.create_user(
        email="john@gestiflow.com",
        password="testpassword123",
        role=role,
        department="it"
    )
    assert user.email == "john@gestiflow.com"
    assert user.role.name == Role.USER
    assert user.department == "it"
    assert user.is_active is True
    assert user.check_password("testpassword123") is True

@pytest.mark.django_db
def test_create_user_raises_value_error():
    with pytest.raises(ValueError, match="The Email field must be set"):
        CustomUser.objects.create_user(email="")

@pytest.mark.django_db
def test_user_api_permissions(api_client, db_roles):
    admin_user = UserFactory(role=db_roles['admin'])
    regular_user = UserFactory(role=db_roles['user'])
    
    url = reverse('user-list')

    # Anonymous user should get 401
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Regular user should get 403 (Forbidden to list all users)
    api_client.force_authenticate(user=regular_user)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Admin user should get 200
    api_client.force_authenticate(user=admin_user)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_user_api_me_endpoint(api_client, db_roles):
    user = UserFactory(role=db_roles['user'], first_name="OldName")
    url = reverse('user-me')

    api_client.force_authenticate(user=user)
    
    # Test GET self
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['email'] == user.email
    assert response.data['first_name'] == "OldName"

    # Test PATCH self
    response = api_client.patch(url, {'first_name': 'NewName'})
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.first_name == "NewName"
