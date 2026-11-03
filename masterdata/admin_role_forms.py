from django import forms
from django.contrib.auth.models import Group, Permission


class PermissionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, permission):
        content_type = permission.content_type
        return f"{content_type.app_label} · {content_type.model} · {permission.name}"


class AdminRoleForm(forms.ModelForm):
    PROTECTED_ROLE_NAMES = {"Administrator", "Admin Toko", "Admin Produksi"}

    permissions = PermissionChoiceField(
        queryset=Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "content_type__model", "codename"
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Permission",
    )

    class Meta:
        model = Group
        fields = ("name", "permissions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["permissions"].widget.attrs.update({"class": "form-check-input"})
        self.fields["name"].help_text = (
            "Nama role harus unik. Nama role inti yang digunakan aplikasi tidak boleh diubah."
        )

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self.instance.pk and self.instance.name in self.PROTECTED_ROLE_NAMES and name != self.instance.name:
            raise forms.ValidationError(
                "Nama role inti tidak boleh diubah karena dipakai oleh aturan akses aplikasi."
            )
        return name
