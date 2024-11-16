from django import forms
from dal import forward
from django.forms import formset_factory
from simo.core.forms import BaseComponentForm, ValueLimitForm
from simo.core.utils.formsets import FormsetField
from simo.core.form_fields import Select2ModelChoiceField
from simo.core.models import Component


class RecuperatorConfig(BaseComponentForm):
    ip_address = forms.GenericIPAddressField(
        help_text="Enter local IP address of your recuperator. <br>"
                  "Make sure you have reserved it on your local router,"
                  "so that it never changes!"
    )
    username = forms.CharField()
    password = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.basic_fields.extend(['ip_address', 'username', 'password'])
        return super().__init__(*args, **kwargs)


class RelatedRecuperatorDataConfig(BaseComponentForm):
    recuperator = Select2ModelChoiceField(
        queryset=Component.objects.filter(
            controller_uid='simo_komfovent.controllers.RecuperatorState'
        ),
        url='autocomplete-component',
        forward=(
            forward.Const([
                'simo_komfovent.controllers.RecuperatorState',
            ], 'controller_uid'),
        )
    )
    widget = forms.ChoiceField(
        initial='numeric-sensor', choices=(
            ('numeric-sensor', "Basic Sensor"),
            ('numeric-sensor-graph', "Graph"),
        )
    )
    limits = FormsetField(
        formset_factory(
            ValueLimitForm, can_delete=True, can_order=True, extra=0, max_num=3
        ), label="Graph Limits"
    )
    value_units = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.basic_fields.append('widget')
        return super().__init__(*args, **kwargs)

    def clean_recuperator(self):
        if self.instance and self.instance.pk:
            org = Component.objects.get(id=self.instance.id)
            if org.config['recuperator'] != self.cleaned_data['recuperator'].id:
                raise forms.ValidationError("This can not be changed!")
        return self.cleaned_data['recuperator']


class FilterContaminationConfigForm(RelatedRecuperatorDataConfig):
    notify_on_level = forms.IntegerField(
        min_value=10, max_value=100, initial=85,
        help_text="Notify instance owners when filter contamination rises "
                  "above this level."
    )

    def __init__(self, *args, **kwargs):
        self.basic_fields.append('notify_on_level')
        return super().__init__(*args, **kwargs)