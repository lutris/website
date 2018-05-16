from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit
from django import forms

from common import models


def get_bootstrap_helper(fields, submit_id, submit_label):
    """ Return a crispy forms helper configured for a Bootstrap3 horizontal
        form.
    """
    helper = FormHelper()
    helper.form_class = "form-horizontal"
    helper.label_class = 'col-lg-4'
    helper.field_class = 'col-lg-8'
    fields.append(
        Div(
            Div(
                Submit(submit_id, submit_label, css_class='btn-default'),
                css_class='col-lg-offset-4 col-lg-8'
            ),
            css_class='form-group'
        )
    )
    helper.layout = Layout(*fields)
    return helper


class Bootstrap3ModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(Bootstrap3ModelForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(list(self.Meta.fields),
                                           'save', 'Save')


class NewsForm(forms.ModelForm):

    # pylint: disable=W0232, R0903
    class Meta:
        model = models.News
        fields = ('title', 'content', 'publish_date', 'image', 'user')


class UploadForm(Bootstrap3ModelForm):
    # pylint: disable=W0232, R0903
    class Meta(object):
        model = models.Upload
        fields = ('uploaded_file', 'destination')
