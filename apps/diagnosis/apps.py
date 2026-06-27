import os
import sys

from django.apps import AppConfig


class DiagnosisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.diagnosis'

    def ready(self):
        # Preload ML weights only in the runserver worker process.
        if 'runserver' not in sys.argv:
            return
        if os.environ.get('RUN_MAIN') != 'true':
            return
        try:
            from .ml_engine import load_models
            load_models()
        except Exception:
            # API calls still return a graceful unavailable response if startup loading fails.
            pass
