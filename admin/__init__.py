"""Administration Module: authorised administrator functions (S2-14).

    from admin import AdminService
    service = AdminService.from_session(session)   # session: GuardedSession
    service.list_users()
"""
from admin.service import AdminError, AdminService, PermissionDeniedError

__all__ = ["AdminError", "AdminService", "PermissionDeniedError"]
