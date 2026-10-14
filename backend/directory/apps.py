from django.apps import AppConfig


class DirectoryConfig(AppConfig):
    name = "directory"
    verbose_name = "Active Directory"

    def ready(self):
        from directory.hooks import register_domain_hooks

        register_domain_hooks()
