# PI1-miniproyecto1-backend

API REST para gestión de usuarios y actividades construida con Django REST Framework y PostgreSQL (Supabase).

## Características

- ✅ CRUD completo para usuarios y actividades
- ✅ Filtros por usuario, estado y prioridad
- ✅ Soporte para sub-tareas
- ✅ Formato de respuesta normalizado
- ✅ Documentación automática con Swagger/OpenAPI
- ✅ Manejo de errores centralizado

## Tecnologías

- Django 5.2
- Django REST Framework 3.16
- PostgreSQL (Supabase)
- drf-spectacular (Swagger/OpenAPI)

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno: `source venv/bin/activate`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Configurar `.env` con credenciales de Supabase
6. Migrar: `python manage.py migrate`
7. Ejecutar: `python manage.py runserver`

## Endpoints

- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **Users**: `/api/users/`
- **Activities**: `/api/activities/`