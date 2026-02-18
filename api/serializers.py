from rest_framework import serializers
from .models import User, Activity


# ========== SERIALIZERS DE MODELOS ==========

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class ActivitySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_id_display', read_only=True)
    status_display = serializers.CharField(source='get_status_id_display', read_only=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Activity
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'parent', 'parent_title',
            'title', 'description',
            'priority_id', 'priority_display',
            'status_id', 'status_display',
            'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ========== SERIALIZERS PARA RESPUESTAS (NUEVOS) ==========

class MetaSerializer(serializers.Serializer):
    """Metadata incluida en todas las respuestas"""
    timestamp = serializers.DateTimeField(help_text="Timestamp ISO 8601 de la respuesta")
    status_code = serializers.IntegerField(help_text="Código HTTP de estado")


class SuccessResponseSerializer(serializers.Serializer):
    """Estructura de respuesta exitosa estándar"""
    success = serializers.BooleanField(default=True, help_text="Indica si la operación fue exitosa")
    data = serializers.JSONField(help_text="Datos de la respuesta", required=False)
    message = serializers.CharField(help_text="Mensaje descriptivo", required=False)
    meta = MetaSerializer(help_text="Metadata de la respuesta")


class UserSuccessResponseSerializer(serializers.Serializer):
    """Respuesta exitosa específica para User"""
    success = serializers.BooleanField(default=True)
    data = UserSerializer(help_text="Datos del usuario")
    message = serializers.CharField(required=False, help_text="Mensaje descriptivo")
    meta = MetaSerializer()


class UserListSuccessResponseSerializer(serializers.Serializer):
    """Respuesta exitosa para lista de usuarios"""
    success = serializers.BooleanField(default=True)
    data = UserSerializer(many=True, help_text="Lista de usuarios")
    meta = MetaSerializer()


class ActivitySuccessResponseSerializer(serializers.Serializer):
    """Respuesta exitosa específica para Activity"""
    success = serializers.BooleanField(default=True)
    data = ActivitySerializer(help_text="Datos de la actividad")
    message = serializers.CharField(required=False, help_text="Mensaje descriptivo")
    meta = MetaSerializer()


class ActivityListSuccessResponseSerializer(serializers.Serializer):
    """Respuesta exitosa para lista de actividades"""
    success = serializers.BooleanField(default=True)
    data = ActivitySerializer(many=True, help_text="Lista de actividades")
    meta = MetaSerializer()


class DeleteSuccessResponseSerializer(serializers.Serializer):
    """Respuesta exitosa para operaciones DELETE"""
    success = serializers.BooleanField(default=True)
    message = serializers.CharField(help_text="Mensaje de confirmación")
    meta = MetaSerializer()


class ValidationErrorDetailSerializer(serializers.Serializer):
    """Detalle de un error de validación por campo"""
    field = serializers.CharField(help_text="Nombre del campo con error")
    message = serializers.CharField(help_text="Mensaje de error del campo")


class ErrorDetailSerializer(serializers.Serializer):
    """Estructura detallada del error"""
    type = serializers.CharField(help_text="Tipo de error (validation_error, not_found, etc)")
    message = serializers.CharField(help_text="Mensaje principal del error")
    code = serializers.IntegerField(help_text="Código HTTP de error")
    errors = ValidationErrorDetailSerializer(many=True, required=False, help_text="Errores específicos de campos")
    details = serializers.JSONField(required=False, help_text="Detalles técnicos adicionales")


class ErrorResponseSerializer(serializers.Serializer):
    """Estructura de respuesta de error estándar"""
    success = serializers.BooleanField(default=False, help_text="Siempre false para errores")
    error = ErrorDetailSerializer(help_text="Detalles del error")
    meta = MetaSerializer(help_text="Metadata de la respuesta")