"""Functions to get rid of spam accounts"""

from django.db.models import Count
from accounts.models import User


def get_no_games_with_website():
    """Return users that have not confirmed their account but have games"""
    return (
        User.objects.annotate(game_count=Count("gamelibrary__games"))
        .filter(email_confirmed=False, game_count=0)
        .exclude(website__exact="")
    )


def get_spam_avatar_users():
    """Return users that have a avatar matching what spam users use"""
    return User.objects.annotate(game_count=Count("gamelibrary__games")).filter(
        avatar__regex=r"/\d{2,3}_.{7}.gif",
        game_count=0,
    )


def get_example_com_users():
    """Return smartasses who are using an example.com email address"""
    return User.objects.filter(email__endswith="@example.com")


def clear_users(users):
    """Delete a list of users"""
    cleared_users = len(users)
    for user in users:
        user.delete()
    return cleared_users
