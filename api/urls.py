from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ActivityViewSet
from api.views.auth import RegisterView, LoginView, MeView, LogoutView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'activities', ActivityViewSet, basename='activity')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('', include(router.urls)),
]