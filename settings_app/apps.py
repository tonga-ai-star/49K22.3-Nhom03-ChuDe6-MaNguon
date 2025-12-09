from django.apps import AppConfig

class SettingsAppConfig(AppConfig):
    name = 'settings_app'
    verbose_name = "Settings"

    def ready(self):
        # import signals
        import settings_app.signals  # noqa
