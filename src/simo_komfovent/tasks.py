import random
from celeryc import celery_app
from django.utils import timezone
from simo.core.models import Instance, Component
from .controllers import RecuperatorFilterContamination



@celery_app.task
def notify_on_clogged_filters():
    from simo.notifications.utils import notify_users
    for instance in Instance.objects.filter(is_active=True):
        timezone.activate(instance.timezone)
        hour = timezone.localtime().hour
        if hour < 7:
            continue
        if hour > 21:
            continue
        if hour % 1 == 0:
            continue
        if not random.choice([True, False, False, False, False]):
            continue

        for comp in Component.objects.filter(
            zone__instance=instance,
            controller_uid=RecuperatorFilterContamination.uid,
        ):
            if comp.value < comp.config.get('notify_on_level'):
                continue

            iusers = comp.zone.instance.instance_users.filter(
                is_active=True, role__is_owner=True
            )
            if iusers:
                notify_users(
                    comp.zone.instance, 'warning',
                    f"Filters are {comp.value}% clogged!",
                    component=comp, instance_users=iusers
                )


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60 * 60, notify_on_clogged_filters.s())