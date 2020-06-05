from django.db.models.functions import Lower
from django.db.models import Count
from accounts.models import User


def get_duplicate_usernames():
    """Return usernames of users that have duplicates"""
    return (
        User
        .objects
        .annotate(uname=Lower('username'))
        .values('uname')
        .annotate(ncnt=Count('uname'))
        .filter(ncnt__gt=1)
    )


def run():
    """Handle duplicate usernames"""
    for username_info in get_duplicate_usernames():
        username = username_info['uname']
        # print("Duplicate username %s" % username)
        users = User.objects.filter(username__iexact=username)
        first_user = users[0]
        other_user = users[1]

        first_has_email = bool(first_user.email)
        other_has_email = bool(other_user.email)
        same_email = first_user.email.lower() == other_user.email.lower()
        first_confirmed = first_user.email_confirmed
        other_confirmed = other_user.email_confirmed
        first_has_games = bool(first_user.gamelibrary.games.count())
        other_has_games = bool(other_user.gamelibrary.games.count())

        if not first_has_email and not first_has_games:
            print("Delete old account with no games: %s" % first_user)
            first_user.delete()
        if not other_has_email and not other_has_games:
            print("Delete other old account with no games: %s" % other_user)
            other_user.delete()

        if (
            not first_confirmed and not first_has_games and
            other_confirmed and other_has_games
        ):
            print("Delete first: %s" % first_user)
            first_user.delete()
        elif (
            first_confirmed and first_has_games and
            not other_confirmed and not other_has_games
        ):
            print("Delete other: %s" % other_user)
            other_user.delete()

        if same_email:
            if not first_confirmed and not other_confirmed:
                if first_has_games and not other_has_games:
                    print("Delete other %s" % other_user)
                    other_user.delete()
                elif not first_has_games and other_has_games:
                    print("Delete first %s" % first_user)
                    first_user.delete()
                elif not first_has_games and not other_has_games:
                    # pick one, doesn't matter which
                    print("Delete other %s" % other_user)
                    other_user.delete()
                elif first_has_games and other_has_games:
                    pass
        else:
            if first_has_email and not other_has_email:
                print("First has email")
                if not other_has_games:
                    print("Deleting the other account %s" % other_user)
                    other_user.delete()
            if other_has_email and not first_has_email:
                print("Other has email")
                if not first_has_games:
                    print("Deleting the first account %s" % first_user)
                    first_user.delete()
            # Figure out what to do here
