import time
from celeryc import celery_app
from django.utils import timezone
from simo.core.middleware import introduce_instance
from simo.core.models import Instance, Component
from simo.automation.helpers import be_or_not_to_be
from .controllers import RecuperatorFilterContamination



@celery_app.task
def notify_on_clogged_filters():
    from simo.notifications.utils import notify_users
    for instance in Instance.objects.filter(is_active=True):
        timezone.activate(instance.timezone)
        introduce_instance(instance)
        hour = timezone.localtime().hour
        if hour < 7:
            continue
        if hour > 21:
            continue

        for comp in Component.objects.filter(
            zone__instance=instance,
            controller_uid=RecuperatorFilterContamination.uid,
        ):
            if comp.value < comp.config.get('notify_on_level'):
                continue

            last_warning = comp.meta.get('last_warning', 0)
            notify = be_or_not_to_be(12 * 60 * 60, 72 * 60 * 60, last_warning)
            if not notify:
                continue

            iusers = comp.zone.instance.instance_users.filter(
                is_active=True, role__is_owner=True
            )
            if iusers:
                notify_users(
                    'warning',
                    f"Filters are {comp.value}% clogged!",
                    component=comp, instance_users=iusers
                )
                comp.meta['last_warning'] = time.time()
                comp.save()


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60 * 60, notify_on_clogged_filters.s())