import sys
import traceback
from simo.core.gateways import BaseObjectCommandsGatewayHandler
from simo.core.forms import BaseGatewayForm
from simo.core.middleware import drop_current_instance
from simo.core.models import Component

from .utils import MODES_MAP



class KomfoventGatewayHandler(BaseObjectCommandsGatewayHandler):
    name = "Komfovent"
    config_form = BaseGatewayForm

    periodic_tasks = (
        ('watch_komfovents', 30),
    )

    sessions = {}

    def watch_komfovents(self):
        from .controllers import RecuperatorState
        drop_current_instance()
        for konfovent_comp in Component.objects.filter(
            controller_uid=RecuperatorState.uid
        ):
            try:
                session = konfovent_comp.controller._fetch_data()
            except Exception as e:
                print(traceback.format_exc(), file=sys.stderr)
                continue
            self.sessions[konfovent_comp.id] = session

    def perform_value_send(self, component, value):
        component.controller.set(value)
        if component.id not in self.sessions:
            return

        id = MODES_MAP[value]['id']

        self.sessions[component.id].post(
            f"http://{component.config['ip_address']}/ajax.xml",
            data=f"3={id}",
        )
