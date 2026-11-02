from django import forms

from .models import Dapur, Jadwal, Toko, TemplateProduk


class BootstrapForm(forms.ModelForm):
    """
    Base ModelForm yang menerapkan class Bootstrap 5 sesuai jenis widget.
    Class CSS yang sudah ada pada widget tetap dipertahankan.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget
            widget_type = widget.__class__.__name__
            existing_classes = widget.attrs.get("class", "").split()

            if widget_type in ("Select", "SelectMultiple"):
                bootstrap_class = "form-select"
            elif widget_type == "CheckboxInput":
                bootstrap_class = "form-check-input"
            else:
                bootstrap_class = "form-control"

            if bootstrap_class not in existing_classes:
                existing_classes.append(bootstrap_class)

            widget.attrs["class"] = " ".join(existing_classes)


class DapurForm(BootstrapForm):
    class Meta:
        model = Dapur
        fields = "__all__"


class JadwalForm(BootstrapForm):
    class Meta:
        model = Jadwal
        fields = "__all__"


class TokoForm(BootstrapForm):
    class Meta:
        model = Toko
        fields = "__all__"


class TemplateProdukForm(BootstrapForm):
    class Meta:
        model = TemplateProduk
        fields = "__all__"
