from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from django.db import IntegrityError
from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view, 
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample  # ← AGREGAR ESTE IMPORT
)
from drf_spectacular.types import OpenApiTypes

from api.views.helpers import (
    success_response,
    handle_not_found,
    handle_validation_error,
    handle_integrity_error
)
from api.models import Activity
from api.serializers import (
    ActivitySerializer,
    ActivitySuccessResponseSerializer,
    ActivityListSuccessResponseSerializer,
    DeleteSuccessResponseSerializer,
    ErrorResponseSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="Listar actividades",
        description="Obtiene una lista paginada de actividades con filtros opcionales",
        parameters=[
            OpenApiParameter(
                name='user',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por ID de usuario',
                required=False
            ),
            OpenApiParameter(
                name='status_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por estado (1=Pendiente, 2=En Progreso, 3=Completada, 4=Cancelada)',
                required=False
            ),
            OpenApiParameter(
                name='priority_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por prioridad (1=Baja, 2=Media, 3=Alta, 4=Urgente)',
                required=False
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ActivityListSuccessResponseSerializer,
                description="Lista de actividades obtenida exitosamente"
            ),
        }
    ),
    create=extend_schema(
        summary="Crear actividad",
        description="Crea una nueva actividad asociada a un usuario",
        request=ActivitySerializer,
        responses={
            201: OpenApiResponse(
                response=ActivitySuccessResponseSerializer,
                description="Actividad creada exitosamente"
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Error de validación o referencia inválida"
            ),
        }
    ),
    retrieve=extend_schema(
        summary="Obtener actividad",
        description="Obtiene los detalles de una actividad específica por su ID",
        responses={
            200: OpenApiResponse(
                response=ActivitySuccessResponseSerializer,
                description="Actividad obtenida exitosamente"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Actividad no encontrada"
            ),
        }
    ),
    update=extend_schema(
        summary="Actualizar actividad",
        description="Actualiza todos los campos de una actividad (PUT). Requiere todos los campos.",
        request=ActivitySerializer,
        responses={
            200: OpenApiResponse(
                response=ActivitySuccessResponseSerializer,
                description="Actividad actualizada exitosamente"
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Error de validación"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Actividad no encontrada"
            ),
        }
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente actividad",
        description="Actualiza solo los campos proporcionados de una actividad (PATCH)",
        request=ActivitySerializer,
        responses={
            200: OpenApiResponse(
                response=ActivitySuccessResponseSerializer,
                description="Actividad actualizada exitosamente"
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Error de validación"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Actividad no encontrada"
            ),
        }
    ),
    destroy=extend_schema(
        summary="Eliminar actividad",
        description="Elimina una actividad del sistema. También eliminará sus sub-tareas asociadas.",
        responses={
            200: OpenApiResponse(
                response=DeleteSuccessResponseSerializer,
                description="Actividad eliminada exitosamente"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Actividad no encontrada"
            ),
        }
    ),
)
class ActivityViewSet(ModelViewSet):
    """ViewSet para gestionar actividades."""
    queryset = Activity.objects.select_related('user', 'parent').all()
    serializer_class = ActivitySerializer
    
    def get_queryset(self):
        """Retorna el queryset con filtros opcionales aplicados."""
        queryset = super().get_queryset()
        
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        status_id = self.request.query_params.get('status_id')
        if status_id:
            queryset = queryset.filter(status_id=status_id)
        
        priority_id = self.request.query_params.get('priority_id')
        if priority_id:
            queryset = queryset.filter(priority_id=priority_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Lista todas las actividades con paginación y filtros opcionales."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Crea una nueva actividad."""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)
        
        try:
            self.perform_create(serializer)
            return success_response(
                data=serializer.data,
                message="Actividad creada exitosamente",
                status_code=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            return handle_integrity_error(e)
    
    def retrieve(self, request, *args, **kwargs):
        """Obtiene una actividad específica por su ID."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(data=serializer.data)
        except Activity.DoesNotExist:
            return handle_not_found('Actividad', kwargs.get('pk'))
    
    def update(self, request, *args, **kwargs):
        """Actualiza completamente una actividad (PUT)."""
        try:
            instance = self.get_object()
        except Activity.DoesNotExist:
            return handle_not_found('Actividad', kwargs.get('pk'))
        
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)
        
        try:
            self.perform_update(serializer)
            return success_response(
                data=serializer.data,
                message="Actividad actualizada exitosamente"
            )
        except IntegrityError as e:
            return handle_integrity_error(e)
    
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente una actividad (PATCH)."""
        try:
            instance = self.get_object()
        except Activity.DoesNotExist:
            return handle_not_found('Actividad', kwargs.get('pk'))
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)
        
        try:
            self.perform_update(serializer)
            return success_response(
                data=serializer.data,
                message="Actividad actualizada exitosamente"
            )
        except IntegrityError as e:
            return handle_integrity_error(e)
    
    def destroy(self, request, *args, **kwargs):
        """Elimina una actividad del sistema."""
        try:
            instance = self.get_object()
            title = instance.title
            subtasks_count = instance.subtasks.count()
            
            self.perform_destroy(instance)
            
            if subtasks_count > 0:
                message = f"Actividad '{title}' y {subtasks_count} sub-tarea(s) eliminadas exitosamente"
            else:
                message = f"Actividad '{title}' eliminada exitosamente"
            
            return success_response(message=message)
        except Activity.DoesNotExist:
            return handle_not_found('Actividad', kwargs.get('pk'))
    
    @extend_schema(
        summary="Sub-tareas de la actividad",
        description="Obtiene todas las sub-tareas (actividades hijas) de una actividad específica",
        responses={
            200: OpenApiResponse(
                response=ActivityListSuccessResponseSerializer,
                description="Lista de sub-tareas"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Actividad no encontrada"
            ),
        }
    )
    @action(detail=True, methods=['get'])
    def subtasks(self, request, pk=None):
        """Obtiene todas las sub-tareas de una actividad."""
        try:
            activity = self.get_object()
            subtasks = activity.subtasks.select_related('user').all()
            serializer = self.get_serializer(subtasks, many=True)
            
            return success_response(
                data=serializer.data,
                message=f"Se encontraron {subtasks.count()} sub-tarea(s)"
            )
        except Activity.DoesNotExist:
            return handle_not_found('Actividad', pk)