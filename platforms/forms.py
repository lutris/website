"""Forms for platform management"""
from games.forms import AutoSlugForm
from . import models


class PlatformForm(AutoSlugForm):
    """Form for game platforms"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Model form configuration"""
        model = models.Platform
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PlatformForm, self).__init__(*args, **kwargs)
        self.fields['default_installer'].required = False
