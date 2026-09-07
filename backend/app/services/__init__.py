"""Business-rule layer. Services compose repositories, enforce permissions,
and raise `app.services.errors.ApiError` subclasses on failure — they never
raise or catch `fastapi.HTTPException` directly, so they stay testable
without spinning up the ASGI app (see `tests/test_permissions.py`).
"""
