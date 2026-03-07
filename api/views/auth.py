from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.authtoken.models import Token
from api.serializers import (
    RegisterSerializer,
    LoginRequestSerializer,
    LoginSuccessResponseSerializer,
    RegisterSuccessResponseSerializer,
    MeSuccessResponseSerializer,
    DeleteSuccessResponseSerializer,
    ErrorResponseSerializer,
)
from api.views.helpers import success_response, handle_authentication_error, handle_validation_error, handle_integrity_error
from api.views.helpers import success_response, handle_authentication_error
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, OpenApiResponse

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @extend_schema(
    summary="Crear cuenta",
    description="Crea un nuevo usuario y devuelve token de autenticación.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=RegisterSuccessResponseSerializer,
            description="Cuenta creada exitosamente"
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Error de validación o email duplicado"
        ),
    },
    tags=["auth"],
    )

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)

        try:
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            return success_response(
                data={
                    "token": token.key,
                    "user": {
                        "id": user.pk,
                        "email": user.email,
                        "name": user.name,
                    },
                },
                message="Cuenta creada exitosamente",
                status_code=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            return handle_integrity_error(e)

class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @extend_schema(
    summary="Iniciar sesión",
    description="Autentica un usuario con email y contraseña y devuelve token.",
    request=LoginRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=LoginSuccessResponseSerializer,
            description="Inicio de sesión exitoso"
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Credenciales inválidas"
        ),
    },
    tags=["auth"],
)
    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        user = authenticate(
            request=request,
            username=email,
            password=password,
        )

        if not user:
            return handle_authentication_error("Credenciales inválidas")

        token, _ = Token.objects.get_or_create(user=user)

        return success_response(
            data={
                "token": token.key,
                "user": {
                    "id": user.pk,
                    "email": user.email,
                },
            },
            message="Inicio de sesión exitoso",
            status_code=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
    summary="Usuario autenticado",
    description="Devuelve la información básica del usuario autenticado.",
    responses={
        200: OpenApiResponse(
            response=MeSuccessResponseSerializer,
            description="Usuario autenticado"
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="No autenticado"
        ),
    },
    tags=["auth"],
)

    def get(self, request):
        return success_response(
            data={
                "id": request.user.pk,
                "email": request.user.email,
            },
            status_code=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
    summary="Cerrar sesión",
    description="Invalida el token del usuario autenticado.",
    responses={
        200: OpenApiResponse(
            response=DeleteSuccessResponseSerializer,
            description="Sesión cerrada"
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="No autenticado"
        ),
    },
    tags=["auth"],
)

    def post(self, request):
        Token.objects.filter(user=request.user).delete()

        return success_response(
            data=None,
            message="Sesión cerrada",
            status_code=status.HTTP_200_OK,
        )