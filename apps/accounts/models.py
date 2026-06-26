from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        try:
            role, _ = Role.objects.get_or_create(name=Role.ADMIN)
            extra_fields.setdefault('role', role)
        except Exception:
            pass

        return self.create_user(email, password, **extra_fields)

class Role(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'

    ROLE_CHOICES = (
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (USER, 'User'),
    )

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

class CustomUser(AbstractUser):
    DEPARTMENT_CHOICES = (
        ('it', 'IT & Development'),
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('sales', 'Sales & Marketing'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    email = models.EmailField('email address', unique=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    avatar = models.FileField(upload_to='avatars/', null=True, blank=True)  # Changed from ImageField to avoid Pillow dependency
    phone = models.CharField(max_length=20, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def has_role(self, role_name):
        return self.role and self.role.name == role_name
