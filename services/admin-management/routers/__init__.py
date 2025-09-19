from .admin import admin_router
from .exams import exam_router
from .subjects import subject_router

__all__ = [
    "admin_router",
    "exam_router",
    "subject_router"
]
