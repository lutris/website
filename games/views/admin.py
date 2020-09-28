"""Custom admin views"""

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from games import models


def redirect_to(request, target):
    """Helper to redirect to the given target"""
    redirect_url = target if target[0] == '/' else request.build_absolute_uri(reverse(target))

    # Enforce https
    if not settings.DEBUG:
        redirect_url = redirect_url.replace('http:', 'https:')

    return redirect(redirect_url)


@staff_member_required
def list_change_submissions_view(request, game_id=None):
    """View to list all change submissions"""

    # Check permissions
    if not request.user.has_perm('games.change_game'):
        return HttpResponseForbidden("You don't have the permission to review changes")

    # Filter changes if a game_id is given
    if game_id:
        game = get_object_or_404(models.Game, id=game_id)
        change_suggestions_unfiltered = models.Game.objects.filter(change_for=game_id)
    else:
        change_suggestions_unfiltered = models.Game.objects.filter(change_for__isnull=False)

    # Populate additional information into the model
    obsolete_changes = 0
    change_suggestions = []
    for change_suggestion in change_suggestions_unfiltered:
        # Generate diff
        diff = change_suggestion.get_changes()

        # If the diff is empty, this change is obsolete and can be deleted
        if not diff:
            change_suggestion.delete()
            obsolete_changes += 1
            continue
        else:
            change_suggestion.diff = diff
            change_suggestions.append(change_suggestion)

        # Populate meta information
        meta = models.GameSubmission.objects.get(game=change_suggestion)
        change_suggestion.author = meta.user
        change_suggestion.reason = meta.reason

    # Determine title
    title = 'Change submissions'
    if game_id:
        title = u"{title} for '{name}'".format(title=title, name=game.name)

    context = dict(
        title=title,
        obsolete_changes=obsolete_changes,
        change_suggestions=change_suggestions,
        for_game=game_id
    )

    return render(request, 'admin/review-change-submissions.html', context)


@staff_member_required
def review_change_submission_view(request, submission_id):
    """View to review a specific change submission"""

    # Check permissions
    if not request.user.has_perm('games.change_game'):
        return HttpResponseForbidden("You don't have the permission to review changes")

    # Fetch game change DB entry
    change_suggestion = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if change_suggestion.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    # Populate diff
    change_suggestion.diff = change_suggestion.get_changes()

    # Populate meta information
    meta = models.GameSubmission.objects.get(game=change_suggestion)
    change_suggestion.author = meta.user
    change_suggestion.reason = meta.reason

    context = dict(
        title='Review change submission',
        change=change_suggestion
    )

    return render(request, 'admin/review-change-submission.html', context)


@staff_member_required
def change_submission_accept(request, submission_id):
    """Accept submission and redirect to overview"""

    # Check permissions
    if not request.user.has_perm('games.change_game'):
        return HttpResponseForbidden("You don't have the permission to review changes")

    # Fetch game change DB entry
    game_changes = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if game_changes.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    # Apply the changes and delete change entry
    game = game_changes.change_for
    game.apply_changes(game_changes)
    game.save()
    game_changes.delete()

    # Redirect
    redirect_target = request.GET.get('redirect', 'admin-change-submissions')
    return redirect_to(request, redirect_target)


@staff_member_required
def change_submission_reject(request, submission_id):
    """Reject submission and redirect to overview"""

    # Check permissions
    if not request.user.has_perm('games.change_game'):
        return HttpResponseForbidden("You don't have the permission to review changes")

    # Fetch game change DB entry
    game_changes = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if game_changes.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    # Delete change entry
    game_changes.delete()

    # Redirect
    redirect_target = request.GET.get('redirect', 'admin-change-submissions')
    return redirect_to(request, redirect_target)
