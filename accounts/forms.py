from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div
from accounts.models import User


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


class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(
            ['username', 'password1', 'password2'], 'register', "Register"
        )


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(
            ['username', 'password'], 'signin', "Sign in"
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('website', 'avatar', 'email')

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(list(self.Meta.fields),
                                           'save', "Save")
