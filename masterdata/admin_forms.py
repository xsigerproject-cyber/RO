from django import forms
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Toko, UserProfile


class AdminUserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Role / Grup",
    )
    toko = forms.ModelChoiceField(
        queryset=Toko.objects.all(),
        required=False,
        label="Toko (khusus Admin Toko)",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active", "groups")
        widgets = {"is_active": forms.CheckboxInput(attrs={"class": "form-check-input"})}

    def clean(self):
        cleaned = super().clean()
        selected_groups = cleaned.get("groups")
        toko = cleaned.get("toko")
        is_admin_toko = selected_groups.filter(name="Admin Toko").exists() if selected_groups is not None else False
        if is_admin_toko and not toko:
            self.add_error("toko", "Toko wajib dipilih untuk role Admin Toko.")
        if not is_admin_toko and toko:
            self.add_error("toko", "Toko hanya boleh diisi untuk role Admin Toko.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            self.save_m2m()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.toko = self.cleaned_data.get("toko")
            profile.save(update_fields=["toko"])
        return user


class AdminSetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Password baru",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Ulangi password baru",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Konfirmasi password tidak sama.")
        if password1 and self.user:
            validate_password(password1, self.user)
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save(update_fields=["password"])
