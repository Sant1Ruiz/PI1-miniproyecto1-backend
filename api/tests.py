from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from api.models import User, Activity


# ─────────────────────────────────────────────
# HELPER: login y obtener token
# ─────────────────────────────────────────────
def get_auth_token(client, email, password):
    """Hace login y retorna el token de autenticación."""
    response = client.post(
        reverse('auth-login'),
        {'email': email, 'password': password},
        format='json'
    )
    return response.data['data']['token']


# ─────────────────────────────────────────────
# AUTH TESTS
# ─────────────────────────────────────────────
class AuthTestCase(APITestCase):
    """
    Tests para los endpoints de autenticación.
    POST /api/auth/login/
    GET  /api/auth/me/
    POST /api/auth/logout/
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='auth@example.com',
            name='Auth User',
            password='password123'
        )
        self.login_url = reverse('auth-login')
        self.me_url = reverse('auth-me')
        self.logout_url = reverse('auth-logout')

    def test_login_success(self):
        """Test: Login exitoso retorna token y datos del usuario"""
        response = self.client.post(
            self.login_url,
            {'email': 'auth@example.com', 'password': 'password123'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data['data'])
        self.assertIn('user', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], 'auth@example.com')

    def test_login_wrong_password(self):
        """Test: Login con contraseña incorrecta retorna 400"""
        response = self.client.post(
            self.login_url,
            {'email': 'auth@example.com', 'password': 'wrongpassword'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_nonexistent_user(self):
        """Test: Login con email inexistente retorna 400"""
        response = self.client.post(
            self.login_url,
            {'email': 'noexiste@example.com', 'password': 'password123'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_missing_fields(self):
        """Test: Login sin campos requeridos retorna 400"""
        response = self.client.post(
            self.login_url,
            {'email': 'auth@example.com'},  # Falta password
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_me_authenticated(self):
        """Test: /me retorna datos del usuario autenticado"""
        token = get_auth_token(self.client, 'auth@example.com', 'password123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'auth@example.com')

    def test_me_unauthenticated(self):
        """Test: /me sin token retorna 401"""
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_logout_success(self):
        """Test: Logout invalida el token"""
        token = get_auth_token(self.client, 'auth@example.com', 'password123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # El token ya no debe funcionar
        response_after = self.client.get(self.me_url)
        self.assertEqual(response_after.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_unauthenticated(self):
        """Test: Logout sin token retorna 401"""
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────
# USER TESTS
# ─────────────────────────────────────────────
class UserViewSetTestCase(APITestCase):
    """
    Tests para el ViewSet de User.
    Cubre todas las operaciones CRUD y casos edge.
    """

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            email='john@example.com',
            name='John Doe',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            email='jane@example.com',
            name='Jane Smith',
            password='password456'
        )

        # Autenticar con user1 por defecto
        token = get_auth_token(self.client, 'john@example.com', 'password123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        self.list_url = reverse('user-list')
        self.detail_url = lambda pk: reverse('user-detail', kwargs={'pk': pk})
        self.activities_url = lambda pk: reverse('user-activities', kwargs={'pk': pk})

    def test_list_users(self):
        """Test: Listar todos los usuarios"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
        self.assertIn('meta', response.data)

    def test_create_user_success(self):
        """Test: Crear un usuario exitosamente"""
        data = {
            'name': 'Alice Johnson',
            'email': 'alice@example.com',
            'password': 'securepass123'
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'alice@example.com')
        self.assertEqual(response.data['message'], 'Usuario creado exitosamente')
        self.assertNotIn('password', response.data['data'])

    def test_create_user_duplicate_email(self):
        """Test: Error al crear usuario con email duplicado"""
        data = {
            'name': 'Duplicate User',
            'email': 'john@example.com',
            'password': 'password123'
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['type'], 'validation_error')
        self.assertIn('email', response.data['error']['errors'][0]['message'].lower())

    def test_create_user_missing_fields(self):
        """Test: Error al crear usuario sin campos requeridos"""
        data = {'name': 'Incomplete User'}

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['type'], 'validation_error')
        self.assertIn('errors', response.data['error'])

    def test_retrieve_user_success(self):
        """Test: Obtener un usuario específico"""
        response = self.client.get(self.detail_url(self.user1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.user1.id)
        self.assertEqual(response.data['data']['email'], 'john@example.com')

    def test_retrieve_user_not_found(self):
        """Test: Error al obtener usuario inexistente"""
        response = self.client.get(self.detail_url(9999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['type'], 'not_found')
        self.assertIn('9999', response.data['error']['message'])

    def test_update_user_success(self):
        """Test: Actualizar usuario completamente (PUT)"""
        data = {
            'name': 'John Updated',
            'email': 'john.updated@example.com',
            'password': 'newpassword123'
        }

        response = self.client.put(self.detail_url(self.user1.id), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'John Updated')
        self.assertEqual(response.data['data']['email'], 'john.updated@example.com')
        self.assertEqual(response.data['message'], 'Usuario actualizado exitosamente')

    def test_partial_update_user_success(self):
        """Test: Actualizar usuario parcialmente (PATCH)"""
        data = {'name': 'John Partially Updated'}

        response = self.client.patch(self.detail_url(self.user1.id), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'John Partially Updated')
        self.assertEqual(response.data['data']['email'], 'john@example.com')

    def test_delete_user_success(self):
        """Test: Eliminar usuario exitosamente"""
        user_id = self.user1.id
        response = self.client.delete(self.detail_url(user_id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminado exitosamente', response.data['message'])
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_user_not_found(self):
        """Test: Error al eliminar usuario inexistente"""
        response = self.client.delete(self.detail_url(9999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_get_user_activities(self):
        """Test: Obtener actividades de un usuario autenticado"""
        Activity.objects.create(
            user=self.user1,
            title='Actividad 1',
            description='Descripción 1',
            priority_id=1,
            status_id=1
        )
        Activity.objects.create(
            user=self.user1,
            title='Actividad 2',
            description='Descripción 2',
            priority_id=2,
            status_id=2
        )

        response = self.client.get(self.activities_url(self.user1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
        self.assertIn('Se encontraron 2 actividades', response.data['message'])


# ─────────────────────────────────────────────
# ACTIVITY TESTS
# ─────────────────────────────────────────────
class ActivityViewSetTestCase(APITestCase):
    """
    Tests para el ViewSet de Activity.
    Cubre todas las operaciones CRUD, filtros y sub-tareas.
    Las actividades requieren autenticación y se filtran por usuario autenticado.
    """

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='password123'
        )

        # Autenticar
        token = get_auth_token(self.client, 'test@example.com', 'password123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        self.activity1 = Activity.objects.create(
            user=self.user,
            title='Actividad 1',
            description='Descripción de actividad 1',
            priority_id=Activity.Priority.ALTA,
            status_id=Activity.Status.PENDIENTE
        )
        self.activity2 = Activity.objects.create(
            user=self.user,
            title='Actividad 2',
            description='Descripción de actividad 2',
            priority_id=Activity.Priority.MEDIA,
            status_id=Activity.Status.EN_PROGRESO
        )

        self.list_url = reverse('activity-list')
        self.detail_url = lambda pk: reverse('activity-detail', kwargs={'pk': pk})
        self.subtasks_url = lambda pk: reverse('activity-subtasks', kwargs={'pk': pk})

    def test_list_activities_unauthenticated(self):
        """Test: Listar actividades sin token retorna 401"""
        self.client.credentials()  # Quitar token
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_activities(self):
        """Test: Listar actividades del usuario autenticado"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)

    def test_list_activities_only_own(self):
        """Test: El usuario solo ve sus propias actividades"""
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User',
            password='password123'
        )
        Activity.objects.create(
            user=other_user,
            title='Actividad de otro usuario',
            description='Descripción',
            priority_id=1,
            status_id=1
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo debe ver las 2 suyas, no la del otro usuario
        self.assertEqual(len(response.data['data']), 2)

    def test_list_activities_filter_by_status(self):
        """Test: Filtrar actividades por estado"""
        response = self.client.get(self.list_url, {'status_id': Activity.Status.PENDIENTE})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(
            response.data['data'][0]['status_id'],
            Activity.Status.PENDIENTE
        )

    def test_list_activities_filter_by_priority(self):
        """Test: Filtrar actividades por prioridad"""
        response = self.client.get(self.list_url, {'priority_id': Activity.Priority.ALTA})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(
            response.data['data'][0]['priority_id'],
            Activity.Priority.ALTA
        )

    def test_create_activity_success(self):
        """Test: Crear actividad — el usuario lo asigna el backend automáticamente"""
        data = {
            'title': 'Nueva Actividad',
            'description': 'Descripción de la nueva actividad',
            'priority_id': Activity.Priority.ALTA,
            'status_id': Activity.Status.PENDIENTE,
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['title'], 'Nueva Actividad')
        self.assertEqual(response.data['message'], 'Actividad creada exitosamente')

    def test_create_activity_assigns_authenticated_user(self):
        """Test: La actividad creada queda asociada al usuario autenticado"""
        data = {
            'title': 'Actividad con usuario automático',
            'description': 'El backend asigna el usuario',
            'priority_id': Activity.Priority.BAJA,
            'status_id': Activity.Status.PENDIENTE
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        activity = Activity.objects.get(id=response.data['data']['id'])
        self.assertEqual(activity.user, self.user)

    def test_create_activity_unauthenticated(self):
        """Test: Crear actividad sin token retorna 401"""
        self.client.credentials()
        data = {
            'title': 'Sin auth',
            'description': 'Descripción',
            'priority_id': 1,
            'status_id': 1
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_activity_with_parent(self):
        """Test: Crear una sub-tarea (actividad con parent)"""
        data = {
            'parent': self.activity1.id,
            'title': 'Sub-tarea',
            'description': 'Esta es una sub-tarea',
            'priority_id': Activity.Priority.BAJA,
            'status_id': Activity.Status.PENDIENTE
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['parent'], self.activity1.id)

    def test_create_activity_missing_required_fields(self):
        """Test: Error al crear actividad sin campos requeridos"""
        data = {}  # Faltan title y description

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['type'], 'validation_error')

    def test_retrieve_activity_success(self):
        """Test: Obtener una actividad específica"""
        response = self.client.get(self.detail_url(self.activity1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.activity1.id)
        self.assertEqual(response.data['data']['title'], 'Actividad 1')

    def test_retrieve_activity_not_found(self):
        """Test: Error al obtener actividad inexistente"""
        response = self.client.get(self.detail_url(9999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['type'], 'not_found')

    def test_update_activity_success(self):
        """Test: Actualizar actividad completamente (PUT)"""
        data = {
            'title': 'Actividad Actualizada',
            'description': 'Descripción actualizada',
            'priority_id': Activity.Priority.ALTA,
            'status_id': Activity.Status.COMPLETADA
        }

        response = self.client.put(self.detail_url(self.activity1.id), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['title'], 'Actividad Actualizada')
        self.assertEqual(response.data['data']['status_id'], Activity.Status.COMPLETADA)

    def test_partial_update_activity_success(self):
        """Test: Actualizar actividad parcialmente (PATCH)"""
        data = {'status_id': Activity.Status.COMPLETADA}

        response = self.client.patch(self.detail_url(self.activity1.id), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status_id'], Activity.Status.COMPLETADA)
        self.assertEqual(response.data['data']['title'], 'Actividad 1')

    def test_delete_activity_success(self):
        """Test: Eliminar actividad exitosamente"""
        activity_id = self.activity1.id
        response = self.client.delete(self.detail_url(activity_id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminada exitosamente', response.data['message'])
        self.assertFalse(Activity.objects.filter(id=activity_id).exists())

    def test_delete_activity_with_subtasks(self):
        """Test: Eliminar actividad con sub-tareas"""
        subtask1 = Activity.objects.create(
            user=self.user,
            parent=self.activity1,
            title='Sub-tarea 1',
            description='Descripción',
            priority_id=1,
            status_id=1
        )
        subtask2 = Activity.objects.create(
            user=self.user,
            parent=self.activity1,
            title='Sub-tarea 2',
            description='Descripción',
            priority_id=1,
            status_id=1
        )

        response = self.client.delete(self.detail_url(self.activity1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('2 sub-tarea(s)', response.data['message'])
        self.assertFalse(Activity.objects.filter(id=subtask1.id).exists())
        self.assertFalse(Activity.objects.filter(id=subtask2.id).exists())

    def test_get_subtasks(self):
        """Test: Obtener sub-tareas de una actividad"""
        Activity.objects.create(
            user=self.user,
            parent=self.activity1,
            title='Sub-tarea 1',
            description='Descripción',
            priority_id=1,
            status_id=1
        )
        Activity.objects.create(
            user=self.user,
            parent=self.activity1,
            title='Sub-tarea 2',
            description='Descripción',
            priority_id=2,
            status_id=1
        )

        response = self.client.get(self.subtasks_url(self.activity1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
        self.assertIn('Se encontraron 2 sub-tarea(s)', response.data['message'])

    def test_get_subtasks_empty(self):
        """Test: Obtener sub-tareas cuando no hay ninguna"""
        response = self.client.get(self.subtasks_url(self.activity1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 0)
        self.assertIn('Se encontraron 0 sub-tarea(s)', response.data['message'])


# ─────────────────────────────────────────────
# RESPONSE FORMAT TESTS
# ─────────────────────────────────────────────
class ResponseFormatTestCase(APITestCase):
    """
    Tests para verificar que el formato de respuesta sea consistente.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='format@example.com',
            name='Format Test',
            password='password123'
        )
        token = get_auth_token(self.client, 'format@example.com', 'password123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_success_response_structure(self):
        """Test: Verificar estructura de respuesta exitosa"""
        response = self.client.get(reverse('user-detail', kwargs={'pk': self.user.id}))

        self.assertIn('success', response.data)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)
        self.assertIn('timestamp', response.data['meta'])
        self.assertIn('status_code', response.data['meta'])
        self.assertTrue(response.data['success'])

    def test_error_response_structure(self):
        """Test: Verificar estructura de respuesta de error"""
        response = self.client.get(reverse('user-detail', kwargs={'pk': 9999}))

        self.assertIn('success', response.data)
        self.assertIn('error', response.data)
        self.assertIn('meta', response.data)
        self.assertFalse(response.data['success'])
        self.assertIn('type', response.data['error'])
        self.assertIn('message', response.data['error'])
        self.assertIn('code', response.data['error'])

    def test_validation_error_response_structure(self):
        """Test: Verificar estructura de error de validación"""
        response = self.client.post(
            reverse('user-list'),
            {'name': 'Test'},  # Falta email y password
            format='json'
        )

        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['type'], 'validation_error')
        self.assertIn('errors', response.data['error'])
        self.assertIsInstance(response.data['error']['errors'], list)

        for error in response.data['error']['errors']:
            self.assertIn('field', error)
            self.assertIn('message', error)


# ─────────────────────────────────────────────
# MODEL TESTS
# ─────────────────────────────────────────────
class ModelTestCase(TestCase):
    """
    Tests para los modelos User y Activity.
    """

    def test_create_user(self):
        """Test: Crear un usuario correctamente"""
        user = User.objects.create_user(
            email='model@example.com',
            name='Model Test',
            password='password123'
        )

        self.assertEqual(user.email, 'model@example.com')
        self.assertEqual(user.name, 'Model Test')
        self.assertTrue(user.check_password('password123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test: Crear un superusuario"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User',
            password='adminpass123'
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str_method(self):
        """Test: Método __str__ del modelo User"""
        user = User.objects.create_user(
            email='str@example.com',
            name='String Test',
            password='password123'
        )

        self.assertEqual(str(user), 'str@example.com')

    def test_create_activity(self):
        """Test: Crear una actividad correctamente"""
        user = User.objects.create_user(
            email='activity@example.com',
            name='Activity Test',
            password='password123'
        )

        activity = Activity.objects.create(
            user=user,
            title='Test Activity',
            description='Test Description',
            priority_id=Activity.Priority.ALTA,
            status_id=Activity.Status.PENDIENTE
        )

        self.assertEqual(activity.title, 'Test Activity')
        self.assertEqual(activity.user, user)
        self.assertEqual(activity.priority_id, Activity.Priority.ALTA)
        self.assertEqual(activity.status_id, Activity.Status.PENDIENTE)

    def test_activity_str_method(self):
        """Test: Método __str__ del modelo Activity"""
        user = User.objects.create_user(
            email='str@example.com',
            name='String Test',
            password='password123'
        )

        activity = Activity.objects.create(
            user=user,
            title='String Activity',
            description='Description',
            priority_id=1,
            status_id=1
        )

        self.assertEqual(str(activity), 'String Activity - str@example.com')

    def test_activity_cascade_delete(self):
        """Test: Eliminar usuario elimina sus actividades (CASCADE)"""
        user = User.objects.create_user(
            email='cascade@example.com',
            name='Cascade Test',
            password='password123'
        )

        activity = Activity.objects.create(
            user=user,
            title='Cascade Activity',
            description='Description',
            priority_id=1,
            status_id=1
        )

        activity_id = activity.id
        user.delete()

        self.assertFalse(Activity.objects.filter(id=activity_id).exists())