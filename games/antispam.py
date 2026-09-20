"""Scoring of game submissions by the lutris-antispam rules.

The rules themselves live in a separate package so they stay out of this public
repository. That package is optional: when it isn't installed the API simply
reports no assessment and moderation carries on unchanged.

Nothing here acts on a verdict. Scoring is advisory and only ever reaches
moderators through the dashboard; deleting or banning stays a human decision.
"""

import logging

from django.conf import settings
from django.core.cache import cache

from common.util import extract_domain

try:
    from lutris_antispam import assess
except ImportError:  # pragma: no cover - depends on the deployment
    assess = None

LOGGER = logging.getLogger(__name__)

SPAM_DOMAINS_CACHE_KEY = "antispam:spam_domains"
SPAM_DOMAINS_CACHE_SECONDS = 300


def get_spam_domains():
    """Domains recorded from submissions a moderator banned.

    Cached briefly: it is read once per submission when a whole moderation page
    is scored, and the list only changes when someone presses the ban button.
    """
    domains = cache.get(SPAM_DOMAINS_CACHE_KEY)
    if domains is None:
        from games.models import SpamDomain

        domains = SpamDomain.known_domains()
        cache.set(SPAM_DOMAINS_CACHE_KEY, domains, SPAM_DOMAINS_CACHE_SECONDS)
    return domains


def is_available():
    """Whether submissions can be scored at all."""
    return assess is not None and getattr(settings, "ANTISPAM_ENABLED", True)


def get_submission_payload(submission, library_game_count=None):
    """Build the dict the scoring rules expect from a GameSubmission."""
    game = submission.game
    user = submission.user
    account_age_days = None
    if user.date_joined and submission.created_at:
        account_age_days = (submission.created_at - user.date_joined).total_seconds() / 86400
    return {
        "name": game.name,
        "description": game.description,
        "website": game.website,
        "reason": submission.reason,
        "user_email": user.email,
        "username": user.username,
        "email_confirmed": user.email_confirmed,
        "profile_website": user.website,
        "account_age_days": account_age_days,
        "library_game_count": library_game_count,
        "platforms": tuple(platform.name for platform in game.platforms.all()),
        "website_seen_in_spam": extract_domain(game.website) in get_spam_domains(),
    }


def assess_submission(submission, library_game_count=None):
    """Return the assessment of a submission as a dict, or None if unavailable.

    A failure to score must never break the moderation queue, so any error from
    the rules is logged and treated as "no assessment".
    """
    if hasattr(submission, "_spam_assessment"):
        return submission._spam_assessment  # pylint: disable=protected-access
    assessment = None
    if is_available():
        try:
            assessment = assess(get_submission_payload(submission, library_game_count)).as_dict()
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Failed to score submission %s", submission.id)
    submission._spam_assessment = assessment  # pylint: disable=protected-access
    return assessment
