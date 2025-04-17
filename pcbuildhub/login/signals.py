from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from builder.models import PCBuild

@receiver(user_logged_in)
def claim_guest_builds(sender, user, request, **kwargs):
    for bid in request.session.get("guest_builds", []):
        try:
            b = PCBuild.objects.get(id=bid, owner__isnull=True)
            b.owner = user
            b.save()
        except PCBuild.DoesNotExist:
            pass
    request.session.pop("guest_builds", None)
