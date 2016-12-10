import factory
from django.utils.text import slugify
from django.db.models.signals import post_save
from platforms.models import Platform
from runners.models import Runner
from games import models
from accounts.models import User
from accounts.signals import create_library


class PlatformFactory(factory.DjangoModelFactory):
    class Meta:
        model = Platform
    name = 'Amiga'


class GenreFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Genre
    name = 'Arcade'


class GameFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Game
    name = factory.Iterator(['Quake', 'Unreal', 'Serious Sam',
                             'Duke 3D', 'Deus Ex'])
    year = 1999
    is_public = True


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
        self.slug = slugify(unicode(self.name))


class InstallerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Installer
    runner = factory.SubFactory(RunnerFactory)
    version = 'test'
    published = True
    user = factory.SubFactory(UserNoLibraryFactory)
