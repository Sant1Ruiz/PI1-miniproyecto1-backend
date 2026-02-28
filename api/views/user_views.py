from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from django.db import IntegrityError
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from api.views.helpers import (
    success_response,
    handle_not_found,
    handle_validation_error,
    handle_integrity_error
)
from api.models import User
from api.serializers import (
    UserSerializer,
    ActivitySerializer,
    ActivityListSuccessResponseSerializer,
    ErrorResponseSerializer
)

from api.views.schemas.user import user_view_schema

@user_view_schema
class UserViewSet(ModelViewSet):
    """
    ViewSet para gestionar usuarios.
    
    Proporciona operaciones CRUD completas para el modelo User.
    Todas las respuestas siguen un formato normalizado para facilitar
    el manejo en el frontend.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def list(self, request, *args, **kwargs):
        """Lista todos los usuarios con paginación opcional."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Crea un nuevo usuario."""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)
        
        try:
            self.perform_create(serializer)
            return success_response(
                data=serializer.data,
                message="Usuario creado exitosamente",
                status_code=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            return handle_integrity_error(e)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un usuario específico por ID."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(data=serializer.data)
        except User.DoesNotExist:
            return handle_not_found('Usuario', kwargs.get('pk'))
    
    def update(self, request, *args, **kwargs):
        """Actualiza completamente un usuario (PUT)."""
        try:
            instance = self.get_object()
        except User.DoesNotExist:
            return handle_not_found('Usuario', kwargs.get('pk'))
        
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)
        
        try:
            self.perform_update(serializer)
            return success_response(
                data=serializer.data,
                message="Usuario actualizado exitosamente"
            )
        except IntegrityError as e:
            return handle_integrity_error(e)
    
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente un usuario (PATCH)."""
        try:
            instance = self.get_object()
        except User.DoesNotExist:
            return handle_not_found('Usuario', kwargs.get('pk'))
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)
        
        try:
            self.perform_update(serializer)
            return success_response(
                data=serializer.data,
                message="Usuario actualizado exitosamente"
            )
        except IntegrityError as e:
            return handle_integrity_error(e)
    
    def destroy(self, request, *args, **kwargs):
        """Elimina un usuario del sistema."""
        try:
            instance = self.get_object()
            email = instance.email
            self.perform_destroy(instance)
            return success_response(
                message=f"Usuario '{email}' eliminado exitosamente"
            )
        except User.DoesNotExist:
            return handle_not_found('Usuario', kwargs.get('pk'))
    
    @extend_schema(
        summary="Actividades del usuario",
        description="Obtiene todas las actividades asociadas a un usuario específico",
        responses={
            200: OpenApiResponse(
                response=ActivityListSuccessResponseSerializer,
                description="Lista de actividades del usuario"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Usuario no encontrado"
            ),
        }
    )
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Obtiene todas las actividades de un usuario."""
        try:
            user = self.get_object()
            activities = user.activities.select_related('parent').all()
            serializer = ActivitySerializer(activities, many=True)
            
            return success_response(
                data=serializer.data,
                message=f"Se encontraron {activities.count()} actividades"
            )
        except User.DoesNotExist:
            return handle_not_found('Usuario', pk)