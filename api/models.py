from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('El usuario debe tener un email')
        
        email = self.normalize_email(email)
        user = self.model(email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Modelo de Usuario personalizado"""
    
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    max_horas_day = models.IntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Campos requeridos por Django Admin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'user'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.email


class Activity(models.Model):
    """Modelo de Actividad"""
    
    # Opciones para ENUM priority_id
    class Priority(models.IntegerChoices):
        BAJA = 1, 'Baja'
        MEDIA = 2, 'Media'
        ALTA = 3, 'Alta'
    
    # Opciones para ENUM status_id
    class Status(models.IntegerChoices):
        PENDIENTE = 1, 'Pendiente'
        EN_PROGRESO = 2, 'En Progreso'
        COMPLETADA = 3, 'Completada'
        CANCELADA = 4, 'Cancelada'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority_id = models.IntegerField(
        choices=Priority.choices,
        default=Priority.MEDIA
    )
    status_id = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDIENTE
    )
    due_date = models.DateTimeField(null=True, blank=True)
    duration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"