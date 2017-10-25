"""Custom admin views"""

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
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

    if game_id:
        game = get_object_or_404(models.Game, id=game_id)
        change_suggestions = models.Game.objects.filter(change_for=game_id)
    else:
        change_suggestions = models.Game.objects.filter(change_for__isnull=False)

    title = 'Change submissions'

    if game_id:
        title = "{title} for '{name}'".format(title=title, name=game.name)

    context = dict(
        title=title,
        change_suggestions=change_suggestions,
        for_game=game_id
    )

    return render(request, 'admin/review-change-submissions.html', context)


@staff_member_required
def review_change_submission_view(request, submission_id):
    """View to review a specific change submission"""

    # Fetch game change DB entry
    game_changes = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if game_changes.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    # Get list of all deltas
    changes = game_changes.get_changes()

    context = dict(
        title='Review change submission',
        submission_id=game_changes.id,
        changes=changes
    )

    return render(request, 'admin/review-change-submission.html', context)


@staff_member_required
def change_submission_accept(request, submission_id):
    """Accept submission and redirect to overview"""

    # Fetch game change DB entry
    game_changes = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if game_changes.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    game = game_changes.change_for
    game.apply_changes(game_changes)
    game.save()
    game_changes.delete()

    redirect_target = request.GET.get('redirect', 'admin-change-submissions')

    return redirect_to(request, redirect_target)


@staff_member_required
def change_submission_reject(request, submission_id):
    """Reject submission and redirect to overview"""

    # Fetch game change DB entry
    game_changes = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if game_changes.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    game_changes.delete()

    redirect_target = request.GET.get('redirect', 'admin-change-submissions')

    return redirect_to(request, redirect_target)
