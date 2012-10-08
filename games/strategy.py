from mithril.strategy import Strategy
from django.conf import settings
from games.models import SiteACL


class DevelStrategy(Strategy):
    # a tuple of `method name` -> `lookup to apply`.
    # if the method does not exist, or returns None, it
    # continues to the next tuple.
    actions = [
        ('view_on_site', 'site_acl__pk'),
    ]

    def view_on_site(self, request, view, *view_args, **view_kwargs):
        try:
            site_acl = SiteACL.objects.get(site=settings.SITE_ID)
            return site_acl.pk
        except SiteACL.DoesNotExist:
            print "pass"
            pass
