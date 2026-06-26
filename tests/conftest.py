import pytest
from rest_framework.test import APIClient
import factory
from apps.accounts.models import CustomUser, Role
from apps.resources.models import Resource, Category

class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
    name = factory.Sequence(lambda n: [Role.ADMIN, Role.MANAGER, Role.USER][n % 3])

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
    email = factory.Sequence(lambda n: f"user{n}@gestiflow.com")
    first_name = "Test"
    last_name = "User"
    is_active = True
    role = factory.SubFactory(RoleFactory)

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
    name = factory.Sequence(lambda n: f"Category {n}")
    description = "Test Category Description"

class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Resource
    title = factory.Sequence(lambda n: f"Resource {n}")
    description = "Test Resource Description"
    status = "active"
    category = factory.SubFactory(CategoryFactory)
    owner = factory.SubFactory(UserFactory)
    is_archived = False

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def db_roles(db):
    admin, _ = Role.objects.get_or_create(name=Role.ADMIN)
    manager, _ = Role.objects.get_or_create(name=Role.MANAGER)
    user, _ = Role.objects.get_or_create(name=Role.USER)
    return {'admin': admin, 'manager': manager, 'user': user}
