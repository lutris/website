import factory
from django.db.models.signals import post_save

from accounts.models import User
from accounts.signals import create_library
from common.util import slugify
from games import models
from platforms.models import Platform
from runners.models import Runner


class PlatformFactory(factory.DjangoModelFactory):
    class Meta:
        model = Platform
        django_get_or_create = ('name',)
    name = factory.Iterator(['Amiga', 'Super Nintendo', 'Sega Genesis', 'Sony Playstation'])


class GenreFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Genre
        django_get_or_create = ('name',)
    name = 'Arcade'


class GameFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Game
    name = factory.Iterator(['Quake', 'Unreal', 'Serious Sam',
                             'Duke 3D', 'Deus Ex'])
    year = 1999
    website = 'example.com'
    description = 'Description'
    platforms = factory.RelatedFactory(PlatformFactory, name='Amiga')
    genres = factory.RelatedFactory(GenreFactory, name='Arcade')
    is_public = True


class GameChangeFactory(factory.DjangoModelFactory):
    """Creates a change row model which is equal to the game given by change_for"""

    class Meta:
        model = models.Game

    name = factory.LazyAttribute(lambda obj: obj.change_for.name)
    year = factory.LazyAttribute(lambda obj: obj.change_for.year)
    website = factory.LazyAttribute(lambda obj: obj.change_for.website)
    description = factory.LazyAttribute(lambda obj: obj.change_for.description)
    is_public = False

    @factory.post_generation
    def platforms(self, create, extracted):
        if not create:
            return

        if extracted:
            for platform in self.change_for.platforms.all():
                self.platforms.add(platform)

    @factory.post_generation
    def genres(self, create, extracted):
        if not create:
            return

        if extracted:
            for genre in self.change_for.genres.all():
                self.genres.add(genre)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
    first_name = "Tester"
    last_name = "Testing"
    username = factory.Sequence(lambda n: 'user%d' % n)
    email = "tester@lutris.net"
    is_active = True
    email_confirmed = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password("password")
        self.save()


class UserNoLibraryFactory(UserFactory):

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        post_save.disconnect(create_library, User)
        user = super(UserFactory, cls)._create(target_class, *args, **kwargs)
        user.set_password('password')
        user.save()
        post_save.connect(create_library, User)
        return user


class GameLibraryFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.GameLibrary
    user = factory.SubFactory(UserNoLibraryFactory)

    @factory.post_generation
    def games(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for game in extracted:
                self.games.add(game)


class RunnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Runner
    name = factory.Sequence(lambda n: 'runner%s' % n)

    @factory.post_generation
    def set_slug(self, create, extracted, **kwargs):
        if not create:
            return
        self.slug = slugify(self.name)


class InstallerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Installer
    runner = factory.SubFactory(RunnerFactory)
    version = 'test'
    published = True
    user = factory.SubFactory(UserNoLibraryFactory)


class CompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Company
        django_get_or_create = ('name',)
    name = factory.Iterator(['Valve', 'CD Projekt', 'Blizzard', 'Tripwire Interactive'])
    slug = factory.Iterator(['valve', 'cd-projekt', 'blizzard', 'tripwire-interactive'])
