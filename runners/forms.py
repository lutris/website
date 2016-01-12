# pylint: disable=W0232,R0903
from games.forms import AutoSlugForm
from . import models


class RunnerForm(AutoSlugForm):

    class Meta:
        model = models.Runner
        fields = '__all__'
