from django.apps import AppConfig


class PrescriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.prescriptions'

    def ready(self):
        import apps.prescriptions.admin
