from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample
)
from api.serializers import (
    UserSerializer,
    UserSuccessResponseSerializer,
    UserListSuccessResponseSerializer,
    DeleteSuccessResponseSerializer,
    ErrorResponseSerializer
)

user_view_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        description="Obtiene una lista paginada de todos los usuarios registrados",
        responses={
            200: OpenApiResponse(
                response=UserListSuccessResponseSerializer,
                description="Lista de usuarios obtenida exitosamente"
            ),
        }
    ),
    create=extend_schema(
        summary="Crear usuario",
        description="Crea un nuevo usuario en el sistema. El email debe ser único.",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSuccessResponseSerializer,
                description="Usuario creado exitosamente"
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Error de validación o email duplicado"
            ),
        },
        examples=[
            OpenApiExample(
                name="Ejemplo de éxito",
                response_only=True,
                status_codes=['201'],
                value={
                    "success": True,
                    "data": {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "created_at": "2025-02-18T10:00:00Z",
                        "updated_at": "2025-02-18T10:00:00Z"
                    },
                    "message": "Usuario creado exitosamente",
                    "meta": {
                        "timestamp": "2025-02-18T10:30:00Z",
                        "status_code": 201
                    }
                }
            ),
            OpenApiExample(
                name="Error de validación",
                response_only=True,
                status_codes=['400'],
                value={
                    "success": False,
                    "error": {
                        "type": "validation_error",
                        "message": "Validation failed",
                        "code": 400,
                        "errors": [
                            {
                                "field": "email",
                                "message": "Este campo es requerido"
                            }
                        ]
                    },
                    "meta": {
                        "timestamp": "2025-02-18T10:30:00Z",
                        "status_code": 400
                    }
                }
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Obtener usuario",
        description="Obtiene los detalles de un usuario específico por su ID",
        responses={
            200: OpenApiResponse(
                response=UserSuccessResponseSerializer,
                description="Usuario obtenido exitosamente"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Usuario no encontrado"
            ),
        },
        examples=[
            OpenApiExample(
                name="Usuario no encontrado",
                response_only=True,
                status_codes=['404'],
                value={
                    "success": False,
                    "error": {
                        "type": "not_found",
                        "message": "Usuario con ID 999 no encontrado",
                        "code": 404
                    },
                    "meta": {
                        "timestamp": "2025-02-18T10:30:00Z",
                        "status_code": 404
                    }
                }
            ),
        ]
    ),
    update=extend_schema(
        summary="Actualizar usuario",
        description="Actualiza todos los campos de un usuario (PUT). Requiere todos los campos.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSuccessResponseSerializer,
                description="Usuario actualizado exitosamente"
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Error de validación"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Usuario no encontrado"
            ),
        }
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente usuario",
        description="Actualiza solo los campos proporcionados de un usuario (PATCH)",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSuccessResponseSerializer,
                description="Usuario actualizado exitosamente"
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Error de validación"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Usuario no encontrado"
            ),
        }
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        description="Elimina un usuario del sistema. También eliminará todas sus actividades asociadas.",
        responses={
            200: OpenApiResponse(
                response=DeleteSuccessResponseSerializer,
                description="Usuario eliminado exitosamente"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Usuario no encontrado"
            ),
        },
        examples=[
            OpenApiExample(
                name="Eliminación exitosa",
                response_only=True,
                status_codes=['200'],
                value={
                    "success": True,
                    "message": "Usuario 'john@example.com' eliminado exitosamente",
                    "meta": {
                        "timestamp": "2025-02-18T10:30:00Z",
                        "status_code": 200
                    }
                }
            ),
        ]
    ),
)
