from django.contrib.auth import authenticate
from django.db import IntegrityError

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from drf_spectacular.utils import extend_schema, OpenApiResponse

from api.serializers import (
    RegisterSerializer,
    LoginRequestSerializer,
    LoginSuccessResponseSerializer,
    RegisterSuccessResponseSerializer,
    MeSuccessResponseSerializer,
    DeleteSuccessResponseSerializer,
    ErrorResponseSerializer,
)
from api.views.helpers import (
    success_response,
    handle_validation_error,
    handle_integrity_error,
)
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
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Credenciales inválidas o campos faltantes"
            ),
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return handle_validation_error(serializer.errors)

        email = serializer.validated_data["email"].strip()
        password = serializer.validated_data["password"]

        user = authenticate(
            request=request,
            username=email,
            password=password,
        )

        if not user:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Credenciales inválidas",
                    "meta": {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        description="Devuelve la información básica del usuario autenticado y permite actualizar su perfil.",
        responses={
            200: OpenApiResponse(
                response=MeSuccessResponseSerializer,
                description="Usuario autenticado o actualizado"
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
                "name": request.user.name,
                "max_horas_day": request.user.max_horas_day,
            },
            status_code=status.HTTP_200_OK,
        )

    def patch(self, request):
        user = request.user
        name = request.data.get("name")
        max_horas_day = request.data.get("max_horas_day")

        if name:
            user.name = name
        if max_horas_day is not None:
            user.max_horas_day = int(max_horas_day)

        user.save()

        return success_response(
            data={
                "id": user.pk,
                "email": user.email,
                "name": user.name,
                "max_horas_day": user.max_horas_day,
            },
            message="Perfil actualizado",
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