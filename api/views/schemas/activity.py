from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view, 
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from api.serializers import (
    ActivitySerializer,
    ActivitySuccessResponseSerializer,
    ActivityListSuccessResponseSerializer,
    DeleteSuccessResponseSerializer,
    ErrorResponseSerializer
)

activity_view_schemas = extend_schema_view(
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
                description='Filtrar por prioridad (1=Baja, 2=Media, 3=Alta)',
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