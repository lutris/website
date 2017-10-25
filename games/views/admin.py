"""Custom admin views"""

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from games import models


def redirect_to(request, target):
    """Helper to redirect to the given target"""
    redirect_url = request.build_absolute_uri(reverse(target))

    # Enforce https
    if not settings.DEBUG:
        redirect_url = redirect_url.replace('http:', 'https:')

    return redirect(redirect_url)


@staff_member_required
def list_change_submissions_view(request):
    """View to list all change submissions"""

    context = dict(
        title='Change submissions',
        change_suggestions=models.Game.objects.filter(change_for__isnull=False)
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

    return redirect_to(request, 'admin-change-submissions')


@staff_member_required
def change_submission_reject(request, submission_id):
    """Reject submission and redirect to overview"""

    # Fetch game change DB entry
    game_changes = get_object_or_404(models.Game, id=submission_id)

    # Sanity check: Must be a change submission
    if game_changes.change_for is None:
        return HttpResponseBadRequest('ID must be one of a change submission')

    game_changes.delete()

    return redirect_to(request, 'admin-change-submissions')

