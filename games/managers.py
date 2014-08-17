from django.db.models import Manager


class ScreenshotManager(Manager):
    def published(self, user=None, is_staff=False):
        query = self.get_query_set()
        query = query.order_by('uploaded_at')
        if is_staff:
            return query
        elif user:
            return query.filter(Q(published=True) | Q(user=user))
        else:
            return query.filter(published=True)
