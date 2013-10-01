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


class RegistrationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_username': "A user with that username already exists.",
        'password_mismatch': "The two password fields didn't match.",
    }
    username = forms.RegexField(
        label="Username", max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=("30 characters max."),
        error_messages={
            'invalid': ("This value may contain only letters, numbers and "
                        "@/./+/-/_ characters.")
        }
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput, max_length=64
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        max_length=64,
        help_text="Enter the same password as above, for verification."
    )

    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.helper = get_bootstrap_helper(
            ['username', 'password1', 'password2'], 'register', "Register"
        )

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


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
