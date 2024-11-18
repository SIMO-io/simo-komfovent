import pytz
import time
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.core.exceptions import ValidationError
from simo.core.controllers import NumericSensor
from simo.core.models import Component
from simo.generic.controllers import StateSelect
from simo.users.utils import get_device_user
from simo.users.middleware import introduce as introduce_user
from .gateways import KomfoventGatewayHandler
from .forms import RecuperatorConfig, RelatedRecuperatorDataConfig


class RecuperatorState(StateSelect):
    gateway_class = KomfoventGatewayHandler
    name = "Recuperator"
    config_form = RecuperatorConfig

    default_config = {'states': []}
    default_value = ''

    def _validate_val(self, value, occasion=None):
        available_options = [s.get('slug') for s in self.component.config.get('states', [])]
        if value not in available_options:
            raise ValidationError("Unsupported value!")
        return value

    def _fetch_data(self, try_no=1):
        comp = self.component
        print(f"Fetch {comp}")
        tz = pytz.timezone(comp.zone.instance.timezone)
        timezone.activate(tz)
        session = requests.Session()
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
            if try_no >= 3:
                self._unalive_komfovent(
                    f"Unreachable on IP: {comp.config['ip_address']}"
                )
                return
            time.sleep(3)
            return self._fetch_data(try_no + 1)

        if resp.status_code != 200:
            if try_no >= 3:
                self._unalive_komfovent(
                    f"Status code: {resp.status_code}"
                )
                return
            time.sleep(3)
            return self._fetch_data(try_no + 1)

        resp_soup = BeautifulSoup(resp.content, features="lxml")

        states_map = {s['id']: s['name'] for s in comp.config['states']}
        for i in range(1, 9):
            el = resp_soup.find(id=f'om-{i}')
            if not el:
                if i == 1:
                    self._unalive_komfovent(
                        f"Unsupported version!"
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
            resp = session.get(
                f"http://{comp.config['ip_address']}/i.asp", timeout=3
            )
        except requests.exceptions.Timeout:
            if try_no >= 3:
                self._unalive_komfovent(
                    f"Timeout of i.asp file"
                )
                return
            time.sleep(3)
            return self._fetch_data(try_no + 1)

        if resp.status_code != 200:
            if try_no >= 5:
                self._unalive_komfovent(
                    f"Status code: {resp.status_code}"
                )
                return
            time.sleep(3)
            return self._fetch_data(try_no + 1)

        resp_soup = BeautifulSoup(resp.content, features="xml")
        try:
            state_name = resp_soup.A.OMO.text.strip()
        except:
            if try_no >= 3:
                self._unalive_komfovent(
                    f"Unsupported i.asp XML"
                )
                return
            time.sleep(3)
            return self._fetch_data(try_no + 1)

        device = get_device_user()
        introduce_user(device)
        komfovent_state = None
        for state in comp.config['states']:
            if state['name'] == state_name:
                komfovent_state = state['slug']
                if comp.value != state['slug']:
                    comp.controller._receive_from_device(state['slug'])
                break

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

        print(f"{comp} value: {komfovent_state}")

        return session


    def _unalive_komfovent(self, msg=None):
        self.component.alive = False
        self.component.error_msg = msg
        self.component.save()
        for related_comp in Component.objects.filter(
            controller_uid__startswith='simo_komfovent',
            config__recuperator=self.component.id
        ):
            related_comp.alive = False
            related_comp.save()


class RecuperatorSupplyTemp(NumericSensor):
    name = 'Recuperator supply temperature'
    gateway_class = KomfoventGatewayHandler
    config_form = RelatedRecuperatorDataConfig
    manual_add = False


class RecuperatorFilterContamination(NumericSensor):
    name = 'Recuperator filter contamination'
    gateway_class = KomfoventGatewayHandler
    config_form = RelatedRecuperatorDataConfig
    manual_add = False