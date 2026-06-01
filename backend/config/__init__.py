# Make Celery optional so the web app still runs before Celery is installed.
try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except ModuleNotFoundError:
    __all__ = ()
