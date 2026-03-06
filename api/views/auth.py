from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.authtoken.models import Token
from api.serializers import RegisterSerializer
from api.views.helpers import success_response, handle_authentication_error, handle_validation_error, handle_integrity_error
from api.views.helpers import success_response, handle_authentication_error
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import IntegrityError


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

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

    def post(self, request):
        Token.objects.filter(user=request.user).delete()

        return success_response(
            data=None,
            message="Sesión cerrada",
            status_code=status.HTTP_200_OK,
        )