from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from simo.core.models import Icon, Gateway, Component
from .utils import MODES_MAP


@receiver(post_save, sender=Component)
def post_recuperator_create(sender, instance, created, *args, **kwargs):
    if not created:
        return

    from .controllers import (
        RecuperatorState, RecuperatorSupplyTemp,
        RecuperatorFilterContamination
    )

    if instance.controller_uid != RecuperatorState.uid:
        return

    instance.config['states'] = []
    for slug, data in MODES_MAP.items():
        instance.config['states'].append({
            'slug': slug, 'id': data['id'], 'icon': data['icon'],
            'name': data['name']
        })
    instance.save()

    icon = Icon.objects.filter(slug='temperature-half').first()
    Component.objects.create(
        name=f"{instance.name} supply temp", icon=icon,
        zone=instance.zone, category=instance.category,
        controller_uid=RecuperatorSupplyTemp.uid,
        gateway=instance.gateway, config={
            'recuperator': instance.id, 'widget': 'numeric-sensor',
            'limits': [
                {'value': -10, 'name': "Freezing"},
                {'value': 14, 'name': "Pleasant"},
                {'value': 30, 'name': "Hot"}
            ]
        }, value_units='°C'
    )

    icon = Icon.objects.filter(slug='grid-5').first()
    Component.objects.create(
        name=f"{instance.name} filter contamination", icon=icon,
        zone=instance.zone, category=instance.category,
        controller_uid=RecuperatorFilterContamination.uid,
        gateway=instance.gateway, config={
            'recuperator': instance.id, 'widget': 'numeric-sensor',
            'limits': [
                {'value': 0, 'name': "Clean"},
                {'value': 100, 'name': "Clogged"}
            ], 'notify_on_level': 85
        }, value_units='%',
    )


@receiver(post_delete, sender=Component)
def post_recuperator_delete(sender, instance, *args, **kwargs):
    from .controllers import (
        RecuperatorState, RecuperatorSupplyTemp,
        RecuperatorFilterContamination
    )

    if instance.controller_uid != RecuperatorState.uid:
        return

    Component.objects.filter(
        controller_uid__startswith='simo_komfovent',
        config__recuperator=instance.id
    ).delete()