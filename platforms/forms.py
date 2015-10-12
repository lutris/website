from games.forms import AutoSlugForm
from . import models


class PlatformForm(AutoSlugForm):

    class Meta:
        model = models.Platform
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PlatformForm, self).__init__(*args, **kwargs)
        self.fields['default_installer'].required = False
