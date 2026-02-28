from rest_framework.views import exception_handler
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework import status as http_status
from api.views.helpers import (
    normalize_error_response,
    handle_validation_error
)


def custom_exception_handler(exc, context):
    """
    Exception handler personalizado para normalizar todas las respuestas de error.
    
    Args:
        exc: La excepción que se lanzó
        context: Contexto de la vista donde ocurrió el error
        
    Returns:
        Response normalizada según nuestro formato
    """
    
    # Llamar al exception handler por defecto primero
    response = exception_handler(exc, context)
    
    # Si no hay respuesta, Django no pudo manejar la excepción
    if response is None:
        return None
    
    # Obtener el código de estado
    status_code = response.status_code
    
    # Manejar NotFound (404)
    if isinstance(exc, NotFound) or status_code == 404:
        # Intentar obtener el nombre del modelo del contexto
        view = context.get('view')
        model_name = getattr(view, 'queryset', None)
        
        if model_name:
            model_name = model_name.model.__name__
        else:
            model_name = "Recurso"
        
        # Intentar obtener el ID del kwargs
        pk = context.get('kwargs', {}).get('pk', 'N/A')
        
        return normalize_error_response(
            message=f"{model_name} con ID {pk} no encontrado",
            error_type="not_found",
            status_code=http_status.HTTP_404_NOT_FOUND
        )
    
    # Manejar ValidationError (400)
    if isinstance(exc, ValidationError) or status_code == 400:
        # Si ya tenemos el formato de errores de DRF
        if hasattr(response, 'data') and isinstance(response.data, dict):
            return handle_validation_error(response.data)
    
    # Manejar 401 Unauthorized
    if status_code == 401:
        return normalize_error_response(
            message="Authentication credentials were not provided or are invalid",
            error_type="authentication_error",
            status_code=http_status.HTTP_401_UNAUTHORIZED
        )
    
    # Manejar 403 Forbidden
    if status_code == 403:
        return normalize_error_response(
            message="You don't have permission to perform this action",
            error_type="permission_denied",
            status_code=http_status.HTTP_403_FORBIDDEN
        )
    
    # Manejar 405 Method Not Allowed
    if status_code == 405:
        return normalize_error_response(
            message=f"Method '{context.get('request').method}' not allowed",
            error_type="method_not_allowed",
            status_code=http_status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    # Manejar otros errores genéricos
    error_message = str(exc)
    if hasattr(response, 'data'):
        if isinstance(response.data, dict):
            error_message = response.data.get('detail', str(exc))
        elif isinstance(response.data, str):
            error_message = response.data
    
    return normalize_error_response(
        message=error_message,
        error_type="error",
        status_code=status_code
    )