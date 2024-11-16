from django.core.exceptions import ValidationError
from simo.core.controllers import NumericSensor
from simo.generic.controllers import StateSelect
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

    def _fetch_data(self):
        pass


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