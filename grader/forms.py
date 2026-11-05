import json

from django import forms
from django.conf import settings

from agent.rules import validate_rules
import analyzers  # noqa: F401  (registers analyzers so rule validation knows their names)


class UploadForm(forms.Form):
    file = forms.FileField(label="C source file (.c)")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".c"):
            raise forms.ValidationError("Only .c files are accepted.")
        if f.size > settings.MAX_UPLOAD_BYTES:
            raise forms.ValidationError(f"File too large (limit {settings.MAX_UPLOAD_BYTES // 1024} KB).")
        data = f.read()
        f.seek(0)
        if b"\x00" in data:
            raise forms.ValidationError("This does not look like a text file.")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise forms.ValidationError("The file must be UTF-8 text.")
        if not data.strip():
            raise forms.ValidationError("The file is empty.")
        return f


class RuleSetForm(forms.Form):
    json_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 28, "class": "form-control font-monospace"}),
                                label="Rules (JSON)")
    note = forms.CharField(required=False, max_length=200, label="Change note")

    def clean_json_text(self):
        text = self.cleaned_data["json_text"]
        try:
            data = json.loads(text)
        except ValueError as e:
            raise forms.ValidationError(f"Not valid JSON: {e}")
        errs = validate_rules(data)
        if errs:
            raise forms.ValidationError(errs)       # every error is shown at once
        return text


class BulkUploadForm(forms.Form):
    archive = forms.FileField(label="ZIP of .c files (file name without .c = student username)")
