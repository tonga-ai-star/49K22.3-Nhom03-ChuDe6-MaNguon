from django.apps import AppConfig

class DebtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'debt'
    verbose_name = 'Quản lý Công nợ'

    def ready(self):
        import debt.signals