import factory

from django.db.models.signals import post_save
from games import models
from accounts.models import User
from accounts.signals import create_library


class PlatformFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Platform
    name = 'Amiga'


class GameFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Game
    name = factory.Iterator(['Quake', 'Unreal', 'Serious Sam',
                             'Duke 3D', 'Deus Ex'])
    year = 1999
    is_public = True


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    first_name = "Tester"
    last_name = "Testing"
    username = factory.Sequence(lambda n: 'user%d' % n)
    email = "tester@lutris.net"
    is_active = True


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
    FACTORY_FOR = models.GameLibrary
    user = factory.SubFactory(UserNoLibraryFactory)

    @factory.post_generation
    def games(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for game in extracted:
                self.games.add(game)


class RunnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Runner
    name = factory.Sequence(lambda n: 'runner%s' % n)


class InstallerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Installer
    runner = factory.SubFactory(RunnerFactory)
    version = 'test'
    published = True
    user = factory.SubFactory(UserNoLibraryFactory)
