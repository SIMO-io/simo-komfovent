import pytz
import time
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from simo.core.gateways import BaseObjectCommandsGatewayHandler
from simo.core.forms import BaseGatewayForm
from simo.core.middleware import drop_current_instance
from simo.core.models import Component
from simo.users.utils import get_device_user
from simo.users.middleware import introduce as introduce_user
from .utils import MODES_MAP



class KomfoventGatewayHandler(BaseObjectCommandsGatewayHandler):
    name = "Komfovent"
    config_form = BaseGatewayForm

    periodic_tasks = (
        ('watch_komfovents', 10),
    )

    sessions = {}

    def watch_komfovents(self):
        from .controllers import RecuperatorState
        drop_current_instance()
        for konfovent_comp in Component.objects.filter(
            controller_uid=RecuperatorState.uid
        ):
            self.fetch_komfovent(konfovent_comp)

    def fetch_komfovent(self, comp, try_no=1):

        tz = pytz.timezone(comp.zone.instance.timezone)
        timezone.activate(tz)
        if comp.id not in self.sessions:
            self.sessions[comp.id] = requests.Session()
        session = self.sessions[comp.id]
        try:
            resp = session.post(
                f"http://{comp.config['ip_address']}",
                data={
                    '1': comp.config['username'],
                    '2': comp.config['password']
                },
                timeout=3
            )
        except requests.exceptions.Timeout:
            if try_no >= 5:
                self.unalive_komfovent(
                    comp, f"Unreachable on IP: {comp.config['ip_address']}"
                )
                return
            time.sleep(3)
            return self.fetch_komfovent(comp, try_no+1)

        if resp.status_code != 200:
            if try_no >= 5:
                self.unalive_komfovent(
                    comp, f"Status code: {resp.status_code}"
                )
                return
            time.sleep(3)
            return self.fetch_komfovent(comp, try_no+1)

        resp_soup = BeautifulSoup(resp.content, features="lxml")

        states_map = {s['id']: s['name'] for s in comp.config['states']}
        for i in range(1, 9):
            el = resp_soup.find(id=f'om-{i}')
            if not el:
                if i == 1:
                    self.unalive_komfovent(
                        comp, f"Unsupported version!"
                    )
                    return
                else:
                    continue
            states_map[i] = el.text.strip()

        states_changed = False
        for state in comp.config['states']:
            if states_map.get(state['id']) \
            and states_map.get(state['id']) != state['name']:
                states_changed = True
                state['name'] = states_map[state['slug']]
        if states_changed:
            comp.save()

        try:
            resp = session.get('http://192.168.0.160/i.asp')
        except requests.exceptions.Timeout:
            if try_no >= 5:
                self.unalive_komfovent(
                    comp, f"Unreachable on IP: {comp.config['ip_address']}"
                )
                return
            time.sleep(3)
            return self.fetch_komfovent(comp, try_no + 1)

        if resp.status_code != 200:
            if try_no >= 5:
                self.unalive_komfovent(
                    comp, f"Status code: {resp.status_code}"
                )
                return
            time.sleep(3)
            return self.fetch_komfovent(comp, try_no+1)

        resp_soup = BeautifulSoup(resp.content, features="xml")
        try:
            state_name = resp_soup.A.OMO.text.strip()
        except:
            if try_no >= 5:
                self.unalive_komfovent(
                    comp, f"Unsupported i.asp XML"
                )
                return
            time.sleep(3)
            return self.fetch_komfovent(comp, try_no + 1)

        device = get_device_user()
        introduce_user(device)
        for state in comp.config['states']:
            if state['name'] == state_name:
                if comp.value != state['slug']:
                    comp.controller._receive_from_device(state['slug'])

        for related_comp in Component.objects.filter(
            controller_uid__startswith='simo_komfovent',
            config__recuperator=comp.id
        ):
            if related_comp.controller_uid.endswith('RecuperatorSupplyTemp'):
                try:
                    related_comp.controller._receive_from_device(
                        float(resp_soup.A.AI0.text.strip().strip('°C').strip())
                    )
                except:
                    related_comp.alive = False
                    related_comp.error_msg = "Bad value from device"
                    related_comp.save()
            if related_comp.controller_uid.endswith(
                'RecuperatorFilterContamination'
            ):
                try:
                    related_comp.controller._receive_from_device(
                        float(resp_soup.A.FCG.text.strip().strip('%').strip())
                    )
                except:
                    related_comp.alive = False
                    related_comp.error_msg = "Bad value from device"
                    related_comp.save()


    def unalive_komfovent(self, comp, msg=None):
        comp.alive = False
        comp.error_msg = msg
        comp.save()
        for related_comp in Component.objects.filter(
            controller_uid__startswith='simo_komfovent',
            config__recuperator=comp.id
        ):
            related_comp.alive = False
            related_comp.save()

    def perform_value_send(self, component, value):
        component.controller.set(value)
        if component.id not in self.sessions:
            return

        id = MODES_MAP[value]['id']

        self.sessions[component.id].post(
            f"http://{component.config['ip_address']}/ajax.xml",
            data=f"3={id}",
        )
