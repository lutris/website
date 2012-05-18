"""Forms for the main app"""
import yaml
from django import forms
from games.models import Installer


class InstallerForm(forms.ModelForm):
    """Form to create and modify installers"""

    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'code-editor',
                                     'spellcheck': 'false'})
    )

    # pylint: disable=W0232, R0903
    class Meta:
        """Form configuration"""
        model = Installer
        exclude = ("user", "slug", "game")

    def clean_content(self):
        """Verify that the content field is valid yaml"""
        yaml_data = self.cleaned_data["content"]
        try:
            yaml_data = yaml.load(yaml_data)
        except yaml.scanner.ScannerError:
            raise forms.ValidationError("Invalid YAML data (scanner error)")
        except yaml.parser.ParserError:
            raise forms.ValidationError("Invalid YAML data (parse error)")
        return yaml.dump(yaml_data, default_flow_style=False)
        #return yaml_data
