from django.apps import AppConfig


class SIMOKomfoventAppConfig(AppConfig):
    name = 'simo_komfovent'

    _setup_done = False

    def ready(self):
        if self._setup_done:
            return
        self._setup_done = True

        from simo.core.models import Gateway

        # Execute the get_or_create logic
        Gateway.objects.get_or_create(
            type='simo_komfovent.gateways.KomfoventGatewayHandler'
        )