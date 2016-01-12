# pylint: disable=R0903
from django.db.models import Manager
from django.db.models import Q, Count


class ScreenshotManager(Manager):
    def published(self, user=None, is_staff=False):
        query = self.get_queryset()
        query = query.order_by('uploaded_at')
        if is_staff:
            return query
        elif user:
            return query.filter(Q(published=True) | Q(uploaded_by=user))
        else:
            return query.filter(published=True)


class GenreManager(Manager):
    def with_games(self):
        from games.models import Game
        genre_list = (
            Game.objects.with_installer()
            .values_list('genres')
            .annotate(g_count=Count('genres'))
            .filter(g_count__gt=0)
        )
        genre_ids = [genre[0] for genre in genre_list]
        return self.get_queryset().filter(id__in=genre_ids)
