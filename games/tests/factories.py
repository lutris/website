import factory

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from games import models
from accounts.models import create_profile


class GameFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Game
    name = factory.Iterator(['Doom', 'Quake', 'Unreal',
                             'Serious Sam', 'Duke 3D'])
    year = 1999


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
        post_save.disconnect(create_profile, User)
        user = super(UserFactory, cls)._create(target_class, *args, **kwargs)
        post_save.connect(create_profile, User)
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
