from rest_framework.response import Response
from rest_framework import status as http_status
from django.db import IntegrityError
from datetime import datetime
from typing import Any, Optional, Dict, List


# ========== FUNCIONES DE NORMALIZACIÓN ==========

def normalize_success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = http_status.HTTP_200_OK,
    meta: Optional[Dict] = None
) -> Response:
    """
    Normaliza todas las respuestas exitosas con un formato consistente.
    
    Formato:
    {
        "success": true,
        "data": {...},           # Opcional: solo si hay data
        "message": "...",        # Opcional: solo si hay mensaje
        "meta": {
            "timestamp": "...",
            "status_code": 200
        }
    }
    
    Args:
        data: Datos a retornar (dict, list, None)
        message: Mensaje descriptivo opcional
        status_code: Código HTTP de respuesta
        meta: Metadata adicional opcional
        
    Returns:
        Response normalizada
    """
    response_data = {
        "success": True
    }
    
    # Agregar data solo si existe
    if data is not None:
        response_data["data"] = data
    
    # Agregar mensaje solo si existe
    if message:
        response_data["message"] = message
    
    # Agregar metadata
    response_meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status_code": status_code
    }
    
    # Agregar metadata adicional si existe
    if meta:
        response_meta.update(meta)
    
    response_data["meta"] = response_meta
    
    return Response(response_data, status=status_code)


def normalize_error_response(
    message: str,
    error_type: str,
    status_code: int = http_status.HTTP_400_BAD_REQUEST,
    errors: Optional[List[Dict]] = None,
    details: Optional[Any] = None
) -> Response:
    """
    Normaliza todas las respuestas de error con un formato consistente.
    
    Formato:
    {
        "success": false,
        "error": {
            "type": "validation_error",
            "message": "Validation failed",
            "code": 400,
            "errors": [...],      # Opcional: errores de campo
            "details": {...}      # Opcional: detalles técnicos
        },
        "meta": {
            "timestamp": "...",
            "status_code": 400
        }
    }
    
    Args:
        message: Mensaje principal del error
        error_type: Tipo de error (validation_error, not_found, etc)
        status_code: Código HTTP de error
        errors: Lista de errores de campo (para validación)
        details: Detalles técnicos adicionales
        
    Returns:
        Response normalizada de error
    """
    error_data = {
        "type": error_type,
        "message": message,
        "code": status_code
    }
    
    # Agregar errores de campo si existen
    if errors:
        error_data["errors"] = errors
    
    # Agregar detalles técnicos si existen
    if details:
        error_data["details"] = details
    
    response_data = {
        "success": False,
        "error": error_data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status_code": status_code
        }
    }
    
    return Response(response_data, status=status_code)


# ========== FUNCIONES AUXILIARES ESPECÍFICAS ==========

def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = http_status.HTTP_200_OK
) -> Response:
    """
    Respuesta exitosa simple.
    Wrapper para normalize_success_response.
    
    Uso:
        return success_response(user_data, "Usuario creado")
    """
    return normalize_success_response(data, message, status_code)


def handle_not_found(model_name: str, pk: Any) -> Response:
    """
    Maneja errores 404 cuando no se encuentra un recurso.
    
    Args:
        model_name: Nombre del modelo (ej: "Usuario", "Actividad")
        pk: ID del recurso buscado
        
    Returns:
        Response 404 normalizada
        
    Ejemplo:
        {
            "success": false,
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
    """
    return normalize_error_response(
        message=f"{model_name} con ID {pk} no encontrado",
        error_type="not_found",
        status_code=http_status.HTTP_404_NOT_FOUND
    )


def handle_validation_error(serializer_errors: Dict) -> Response:
    """
    Maneja errores de validación de serializers.
    Convierte los errores de Django REST Framework a nuestro formato.
    
    Args:
        serializer_errors: Dict de errores del serializer.errors
        
    Returns:
        Response 400 normalizada
        
    Ejemplo:
        {
            "success": false,
            "error": {
                "type": "validation_error",
                "message": "Validation failed",
                "code": 400,
                "errors": [
                    {
                        "field": "email",
                        "message": "Este campo es requerido"
                    },
                    {
                        "field": "name",
                        "message": "Este campo no puede estar vacío"
                    }
                ]
            },
            "meta": {
                "timestamp": "2025-02-18T10:30:00Z",
                "status_code": 400
            }
        }
    """
    # Convertir errores de DRF a nuestro formato
    formatted_errors = []
    
    for field, messages in serializer_errors.items():
        # Los mensajes pueden ser una lista o un string
        if isinstance(messages, list):
            for message in messages:
                formatted_errors.append({
                    "field": field,
                    "message": str(message)
                })
        else:
            formatted_errors.append({
                "field": field,
                "message": str(messages)
            })
    
    return normalize_error_response(
        message="Validation failed",
        error_type="validation_error",
        status_code=http_status.HTTP_400_BAD_REQUEST,
        errors=formatted_errors
    )


def handle_integrity_error(e: IntegrityError) -> Response:
    """
    Maneja errores de integridad de base de datos.
    Detecta el tipo de error y genera un mensaje apropiado.
    
    Args:
        e: Excepción IntegrityError de Django
        
    Returns:
        Response 400 normalizada
        
    Ejemplo:
        {
            "success": false,
            "error": {
                "type": "integrity_error",
                "message": "Email already exists",
                "code": 400,
                "details": {
                    "constraint": "unique",
                    "field": "email"
                }
            },
            "meta": {
                "timestamp": "2025-02-18T10:30:00Z",
                "status_code": 400
            }
        }
    """
    error_message = str(e)
    error_message_lower = error_message.lower()
    
    # Detectar tipo de error y mensaje apropiado
    if 'unique constraint' in error_message_lower or 'duplicate' in error_message_lower:
        message = "A record with this data already exists"
        constraint_type = "unique"
        
        # Intentar extraer el campo del error
        field = None
        if 'email' in error_message_lower:
            field = "email"
            message = "Email already exists"
        elif 'name' in error_message_lower:
            field = "name"
            message = "Name already exists"
            
    elif 'foreign key' in error_message_lower:
        message = "Invalid reference to another record"
        constraint_type = "foreign_key"
        field = None
        
    elif 'not null' in error_message_lower:
        message = "Required field is missing"
        constraint_type = "not_null"
        field = None
        
    else:
        message = "Database integrity error"
        constraint_type = "unknown"
        field = None
    
    # Construir detalles del error
    error_details = {
        "constraint": constraint_type,
        "technical_message": error_message
    }
    
    if field:
        error_details["field"] = field
    
    return normalize_error_response(
        message=message,
        error_type="integrity_error",
        status_code=http_status.HTTP_400_BAD_REQUEST,
        details=error_details
    )


def handle_permission_error(message: str = "You don't have permission to perform this action") -> Response:
    """
    Maneja errores de permisos (403 Forbidden).
    
    Args:
        message: Mensaje personalizado
        
    Returns:
        Response 403 normalizada
    """
    return normalize_error_response(
        message=message,
        error_type="permission_denied",
        status_code=http_status.HTTP_403_FORBIDDEN
    )


def handle_authentication_error(message: str = "Authentication credentials were not provided") -> Response:
    """
    Maneja errores de autenticación (401 Unauthorized).
    
    Args:
        message: Mensaje personalizado
        
    Returns:
        Response 401 normalizada
    """
    return normalize_error_response(
        message=message,
        error_type="authentication_error",
        status_code=http_status.HTTP_401_UNAUTHORIZED
    )


def handle_server_error(message: str = "Internal server error") -> Response:
    """
    Maneja errores internos del servidor (500).
    
    Args:
        message: Mensaje descriptivo del error
        
    Returns:
        Response 500 normalizada
    """
    return normalize_error_response(
        message=message,
        error_type="server_error",
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR
    )