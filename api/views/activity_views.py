from datetime import date

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from typing import cast
from rest_framework.request import Request
from django.db import IntegrityError
from django.db.models import Sum
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
from api.models import Activity
from api.serializers import (
    ActivitySerializer,
    ActivityListSuccessResponseSerializer,
    ErrorResponseSerializer
)

from api.views.schemas.activity import activity_view_schemas

@activity_view_schemas
class ActivityViewSet(ModelViewSet):
    """ViewSet para gestionar actividades."""
    queryset = Activity.objects.select_related('user', 'parent').all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
    
        request = cast(Request, self.request)

        queryset = Activity.objects.select_related('user', 'parent').filter(user=request.user)

        status_id = request.query_params.get('status_id')
        if status_id:
            queryset = queryset.filter(status_id=status_id)

        priority_id = request.query_params.get('priority_id')
        if priority_id:
            queryset = queryset.filter(priority_id=priority_id)

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
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
            subtasks = activity.subtasks.select_related('user').filter(user=request.user)
            serializer = self.get_serializer(subtasks, many=True)
            
            return success_response(
                data=serializer.data,
                message=f"Se encontraron {subtasks.count()} sub-tarea(s)"
            )
        except Activity.DoesNotExist:
            return handle_not_found('Actividad', pk)
        


    @action(detail=False, methods=['get'], url_path='totalhours')
    def total_hours(self, request):
        """Obtiene el total de horas registradas en sub-actividades para una fecha."""
        
        request = cast(Request, request)

        query_date = request.query_params.get("date")

        if not query_date:
            query_date = date.today()

        queryset = Activity.objects.filter(
            user=request.user,
            parent__isnull=False,
            due_date=query_date
        )

        total = queryset.aggregate(total_hours=Sum("duration"))

        return success_response(
            data={
                "date": query_date,
                "total_hours": total["total_hours"] or 0,
                "total_subtasks": queryset.count()
            },
            message="Resumen de horas del {date} obtenido exitosamente".format(date=query_date)
        )