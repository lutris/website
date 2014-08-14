from django.db.models import Manager


class ScreenshotManager(Manager):
    def published(self):
        return self.get_query_set().filter(published=True).order_by('uploaded_at')
