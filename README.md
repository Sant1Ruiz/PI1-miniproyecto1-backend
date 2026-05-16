
# PI1-miniproyecto1-backend

API REST para gestión de usuarios y actividades construida con Django REST Framework y PostgreSQL.

---

## Características

-   CRUD completo para usuarios y actividades
-   Filtros por usuario, estado y prioridad
-   Soporte para sub-tareas
-   Respuestas normalizadas
-   Documentación automática con Swagger/OpenAPI
-   Manejo centralizado de errores

---

## Tecnologías

-   Python 3.10.12
-   Django 5.2
-   Django REST Framework 3.16
-   PostgreSQL
-   Supabase
-   drf-spectacular
-   django-cors-headers

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd PI1-miniproyecto1-backend
```


### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

#### Linux/macOS

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Migraciones

Ejecutar migraciones de base de datos:

```bash
python manage.py migrate
```

---

## Ejecutar servidor

```bash
python manage.py runserver
```

Servidor disponible en:

```txt
http://127.0.0.1:8000/
```

---

## API Documentation

### Swagger UI

```txt
http://127.0.0.1:8000/api/docs/
```

### OpenAPI Schema

```txt
http://127.0.0.1:8000/api/schema/
```

## Testing

Ejecutar test y Coverage
```bash
coverage run --source='.' manage.py test api --verbosity=2 --keepdb
coverage report
```