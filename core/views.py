from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.utils.timezone import now


def health_check(request):
    """
    Verifies application and database connectivity.
    """
    db_status = "ok"

    try:
        connections["default"].cursor()
    except OperationalError:
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"

    return JsonResponse(
        {
            "status": status,
            "timestamp": now().isoformat(),
            "database": db_status,
        },
        status=200 if status == "ok" else 503,
    )

def api_root(request):
    return JsonResponse(
        {
            "service": "Activivalles API",
            "version": "1.0.0",
            "status": "running",
            "documentation": "/api/docs/",
        }
    )