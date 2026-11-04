import logging
import os
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .admin_forms import AdminSetPasswordForm, AdminUserForm
from .admin_role_forms import AdminRoleForm
from .models import UserProfile
from .permissions import is_administrator

logger = logging.getLogger(__name__)
User = get_user_model()
BACKUP_DIR = Path(os.getenv("DB_BACKUP_DIR", "/var/backups/ro"))
BACKUP_NAME_RE = re.compile(r"^ro_db_\d{8}_\d{6}_[a-f0-9]{8}\.dump$")


def _admin_only(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_administrator(request.user):
            return HttpResponseForbidden("Hanya Administrator yang dapat mengakses modul administrasi.")
        return view(request, *args, **kwargs)
    return wrapped


def _is_active_administrator(user):
    return user.is_active and (user.is_superuser or user.groups.filter(name="Administrator").exists())


def _has_other_active_administrator(user):
    return User.objects.filter(is_active=True, groups__name="Administrator").exclude(pk=user.pk).exists() or User.objects.filter(is_active=True, is_superuser=True).exclude(pk=user.pk).exists()


def _db_env():
    db = settings.DATABASES["default"]
    return {
        "PGHOST": str(db.get("HOST") or "localhost"),
        "PGPORT": str(db.get("PORT") or "5432"),
        "PGDATABASE": str(db["NAME"]),
        "PGUSER": str(db["USER"]),
        "PGPASSWORD": str(db.get("PASSWORD") or ""),
    }


def _run_db_command(args, timeout=1800):
    env = os.environ.copy()
    env.update(_db_env())
    env["PGCONNECT_TIMEOUT"] = "15"
    result = subprocess.run(
        args, env=env, capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode != 0:
        logger.error("Database utility failed (%s): %s", args[0], result.stderr[-4000:])
        raise RuntimeError(result.stderr[-1500:] or f"{args[0]} gagal.")
    return result


def _create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    filename = f"ro_db_{stamp}_{uuid.uuid4().hex[:8]}.dump"
    path = BACKUP_DIR / filename
    _run_db_command([
        "pg_dump", "--format=custom", "--file", str(path),
    ])
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("File backup tidak terbentuk atau kosong.")
    _run_db_command(["pg_restore", "--list", str(path)], timeout=120)
    return path


def _backup_files():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(BACKUP_DIR.glob("ro_db_*.dump"), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.is_file() and BACKUP_NAME_RE.fullmatch(path.name):
            files.append({"name": path.name, "size": path.stat().st_size, "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone())})
    return files


@_admin_only
def admin_home(request):
    return render(request, "admin_tools/home.html", {
        "user_count": User.objects.count(),
        "active_user_count": User.objects.filter(is_active=True).count(),
        "backup_count": len(_backup_files()),
    })


@_admin_only
def user_list(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.prefetch_related("groups").select_related("profile").order_by("username")
    if query:
        users = users.filter(
            models.Q(username__icontains=query)
            | models.Q(first_name__icontains=query)
            | models.Q(last_name__icontains=query)
            | models.Q(email__icontains=query)
        )
    return render(request, "admin_tools/user_list.html", {"users": users, "query": query})


@_admin_only
def user_create(request):
    form = AdminUserForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            user.set_unusable_password()
            user.save(update_fields=["password"])
            messages.success(
                request,
                f"User {user.username} berhasil dibuat. Atur password melalui menu Ganti Password.",
            )
            return redirect("admin_user_list")
    return render(
        request,
        "admin_tools/user_form.html",
        {"form": form, "page_title": "Tambah User"},
    )


@_admin_only
def user_edit(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser and not request.user.is_superuser:
        return HttpResponseForbidden("Hanya superuser yang dapat mengubah akun superuser.")
    form = AdminUserForm(request.POST or None, instance=target)
    if request.method == "POST" and form.is_valid():
        if target.pk == request.user.pk and not form.cleaned_data.get("is_active"):
            form.add_error("is_active", "Anda tidak dapat menonaktifkan akun yang sedang digunakan.")
        elif _is_active_administrator(target) and (not form.cleaned_data.get("is_active") or not form.cleaned_data.get("groups").filter(name="Administrator").exists()) and not _has_other_active_administrator(target):
            form.add_error("groups", "Tidak boleh menonaktifkan atau menghapus role Administrator aktif terakhir.")
        else:
            form.save()
            messages.success(request, f"User {target.username} berhasil diperbarui.")
            return redirect("admin_user_list")
    return render(request, "admin_tools/user_form.html", {"form": form, "page_title": f"Ubah User: {target.username}", "target": target})


@_admin_only
def user_password(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser and not request.user.is_superuser:
        return HttpResponseForbidden("Hanya superuser yang dapat mengganti password akun superuser.")
    form = AdminSetPasswordForm(request.POST or None, user=target)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Password user {target.username} berhasil diganti.")
        return redirect("admin_user_list")
    return render(request, "admin_tools/password_form.html", {"form": form, "target": target})


@_admin_only
@require_POST
def user_delete(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        messages.error(request, "Akun yang sedang digunakan tidak dapat dihapus.")
    elif target.is_superuser:
        messages.error(request, "Akun superuser tidak dapat dihapus melalui modul ini.")
    elif _is_active_administrator(target) and not _has_other_active_administrator(target):
        messages.error(request, "Administrator aktif terakhir tidak dapat dihapus.")
    else:
        username = target.username
        target.delete()
        messages.success(request, f"User {username} berhasil dihapus.")
    return redirect("admin_user_list")


@_admin_only
def role_list(request):
    roles = Group.objects.annotate(user_count=Count("user", distinct=True)).order_by("name")
    return render(request, "admin_tools/role_list.html", {
        "roles": roles,
        "protected_roles": AdminRoleForm.PROTECTED_ROLE_NAMES,
    })


@_admin_only
def role_create(request):
    form = AdminRoleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        role = form.save()
        messages.success(request, f"Role {role.name} berhasil dibuat.")
        return redirect("admin_role_list")
    return render(request, "admin_tools/role_form.html", {
        "form": form, "page_title": "Tambah Role", "is_protected": False,
    })


@_admin_only
def role_edit(request, group_id):
    target = get_object_or_404(Group, pk=group_id)
    form = AdminRoleForm(request.POST or None, instance=target)
    if request.method == "POST" and form.is_valid():
        role = form.save()
        messages.success(request, f"Permission role {role.name} berhasil diperbarui.")
        return redirect("admin_role_list")
    return render(request, "admin_tools/role_form.html", {
        "form": form,
        "page_title": f"Ubah Role: {target.name}",
        "is_protected": target.name in AdminRoleForm.PROTECTED_ROLE_NAMES,
        "target": target,
    })


@_admin_only
@require_POST
def role_delete(request, group_id):
    target = get_object_or_404(Group.objects.annotate(user_count=Count("user", distinct=True)), pk=group_id)
    if target.name in AdminRoleForm.PROTECTED_ROLE_NAMES:
        messages.error(request, f"Role inti {target.name} tidak dapat dihapus karena digunakan oleh aturan akses aplikasi.")
    elif target.user_count:
        messages.error(request, f"Role {target.name} masih digunakan oleh {target.user_count} user. Lepaskan role dari semua user terlebih dahulu.")
    else:
        name = target.name
        target.delete()
        messages.success(request, f"Role {name} berhasil dihapus.")
    return redirect("admin_role_list")


@_admin_only
def backup_home(request):
    return render(request, "admin_tools/backup.html", {"backups": _backup_files()})


@_admin_only
@require_POST
def backup_create(request):
    try:
        path = _create_backup()
        messages.success(request, f"Backup berhasil dibuat: {path.name}")
    except Exception:
        logger.exception("Pembuatan backup database gagal.")
        messages.error(request, "Backup gagal. Periksa log server dan konfigurasi PostgreSQL client.")
    return redirect("admin_backup")


@_admin_only
def backup_download(request, filename):
    if not BACKUP_NAME_RE.fullmatch(filename):
        raise Http404
    path = BACKUP_DIR / filename
    if not path.is_file():
        raise Http404
    return FileResponse(path.open("rb"), as_attachment=True, filename=filename)


@_admin_only
def restore_home(request):
    return render(request, "admin_tools/restore.html", {"backups": _backup_files()})


@_admin_only
@require_POST
def restore_database(request):
    uploaded = request.FILES.get("backup_file")
    confirmation = request.POST.get("confirmation", "").strip()
    if confirmation != "RESTORE DATABASE":
        messages.error(request, "Konfirmasi harus diketik persis: RESTORE DATABASE.")
        return redirect("admin_restore")
    if not uploaded:
        messages.error(request, "Pilih file backup terlebih dahulu.")
        return redirect("admin_restore")
    if not uploaded.name.lower().endswith(".dump"):
        messages.error(request, "File restore harus berakhiran .dump (format PostgreSQL custom).")
        return redirect("admin_restore")
    if uploaded.size > 1024 * 1024 * 1024:
        messages.error(request, "Ukuran file backup maksimal 1 GB.")
        return redirect("admin_restore")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = BACKUP_DIR / f"restore_upload_{uuid.uuid4().hex}.dump"
    try:
        with temp_path.open("wb") as destination:
            for chunk in uploaded.chunks():
                destination.write(chunk)
        _run_db_command(["pg_restore", "--list", str(temp_path)], timeout=120)
        safety_backup = _create_backup()
        _run_db_command([
            "pg_restore", "--clean", "--if-exists", "--no-owner",
            "--no-privileges", "--exit-on-error", "--single-transaction",
            "--dbname", settings.DATABASES["default"]["NAME"], str(temp_path),
        ])
        messages.success(
            request,
            f"Restore selesai. Backup kondisi sebelum restore tersimpan sebagai {safety_backup.name}. "
            "Silakan login kembali jika sesi berubah."
        )
    except Exception:
        logger.exception("Restore database gagal.")
        messages.error(
            request,
            "Restore gagal. Proses restore dijalankan dalam satu transaksi sehingga perubahan parsial dibatalkan. "
            "Periksa log server."
        )
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Tidak dapat menghapus file upload restore sementara.")
    return redirect("admin_restore")


# Odoo 19 connection configuration (phase 1 only).
from urllib.parse import urlparse

import requests
from cryptography.fernet import Fernet, InvalidToken
from django import forms

from .models import OdooConnectionSetting


class OdooConnectionForm(forms.Form):
    base_url = forms.URLField(label="URL Odoo", max_length=500, widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://perusahaan.odoo.com"}))
    database = forms.CharField(label="Database", max_length=120, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label="User Integrasi", max_length=150, widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    api_key = forms.CharField(label="API Key", required=False, strip=False, widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password", "placeholder": "Kosongkan untuk mempertahankan API Key lama"}))


def _odoo_fernet():
    encryption_key = getattr(settings, "ODOO_API_ENCRYPTION_KEY", "")
    if not encryption_key:
        raise ValueError("Kunci enkripsi Odoo belum dikonfigurasi pada environment server.")
    try:
        return Fernet(encryption_key.encode("ascii"))
    except (ValueError, TypeError):
        raise ValueError("Format ODOO_API_ENCRYPTION_KEY tidak valid. Gunakan kunci Fernet yang dibuat oleh cryptography.")


@_admin_only
def odoo_connection_settings(request):
    config = OdooConnectionSetting.objects.filter(pk=1).first()
    if request.method == "POST":
        form = OdooConnectionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if config is None and not data["api_key"]:
                form.add_error("api_key", "API Key wajib diisi untuk konfigurasi pertama.")
            if not form.errors:
                if config is None:
                    config = OdooConnectionSetting(pk=1)
                config.base_url = data["base_url"].rstrip("/")
                config.database = data["database"].strip()
                config.username = data["username"].strip()
                if data["api_key"]:
                    try:
                        config.api_key_encrypted = _odoo_fernet().encrypt(data["api_key"].encode()).decode("ascii")
                    except ValueError as exc:
                        form.add_error("api_key", str(exc))
                if form.errors:
                    return render(request, "admin_tools/odoo_connection.html", {"form": form, "config": config, "has_api_key": bool(config and config.api_key_encrypted)})
                config.save()
                if request.POST.get("action") == "test":
                    try:
                        parsed = urlparse(config.base_url)
                        if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password:
                            raise ValueError("URL Odoo tidak valid.")
                        if parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1"):
                            raise ValueError("Koneksi Odoo wajib menggunakan HTTPS.")
                        key = _odoo_fernet().decrypt(config.api_key_encrypted.encode("ascii")).decode("utf-8")
                        headers = {
                            "Authorization": f"bearer {key}",
                            "Content-Type": "application/json",
                            "User-Agent": "RO-Operations/1.0",
                        }
                        if config.database:
                            headers["X-Odoo-Database"] = config.database
                        response = requests.post(
                            config.base_url + "/json/2/res.users/context_get",
                            headers=headers, json={}, timeout=(5, 15), allow_redirects=False,
                        )
                        if response.status_code == 200:
                            config.connection_status = "success"
                            config.connection_message = "Koneksi berhasil. Odoo menerima autentikasi API Key."
                            messages.success(request, config.connection_message)
                        elif response.status_code in (401, 403):
                            raise ValueError("Autentikasi ditolak Odoo. Periksa API Key dan hak akses user integrasi.")
                        elif response.status_code == 404:
                            raise ValueError("Endpoint JSON-2 tidak ditemukan. Pastikan server menggunakan Odoo 19 dan URL benar.")
                        elif response.is_redirect:
                            raise ValueError("Odoo mengalihkan koneksi. Periksa URL dasar dan HTTPS.")
                        else:
                            raise ValueError(f"Odoo merespons HTTP {response.status_code}. Periksa URL dan database.")
                    except (requests.RequestException, ValueError, InvalidToken) as exc:
                        config.connection_status = "failed"
                        config.connection_message = str(exc)[:500]
                        messages.error(request, config.connection_message)
                    config.last_tested_at = timezone.now()
                    config.save(update_fields=["connection_status", "connection_message", "last_tested_at", "updated_at"])
                else:
                    config.connection_status = "untested"
                    config.connection_message = "Konfigurasi disimpan. Jalankan Test Connection untuk memeriksa koneksi."
                    config.save(update_fields=["connection_status", "connection_message", "updated_at"])
                    messages.success(request, "Pengaturan koneksi Odoo berhasil disimpan.")
                return redirect("admin_odoo_connection")
    else:
        form = OdooConnectionForm(initial={
            "base_url": config.base_url if config else "",
            "database": config.database if config else "",
            "username": config.username if config else "",
        })
    return render(request, "admin_tools/odoo_connection.html", {
        "form": form,
        "config": config,
        "has_api_key": bool(config and config.api_key_encrypted),
    })
