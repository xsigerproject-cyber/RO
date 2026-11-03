from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from .models import Dapur, Jadwal, RO, Toko, TemplateProduk
from .permissions import (
    is_administrator, is_admin_produksi, is_admin_toko, can_access_ro,
)


def _user_store(user):
    profile = getattr(user, "profile", None)
    return profile.toko if profile else None


def _ro_queryset(user):
    qs = RO.objects.select_related("toko", "dapur", "jadwal", "produk", "dibuat_oleh")
    if is_admin_toko(user) and not is_administrator(user):
        toko = _user_store(user)
        return qs.filter(toko=toko) if toko else qs.none()
    return qs


@login_required
@require_http_methods(["GET", "POST"])
def ro_transaksi(request):
    if not can_access_ro(request.user):
        return HttpResponseForbidden("Akun Anda tidak memiliki akses transaksi RO.")

    toko_user = _user_store(request.user)
    toko_options = Toko.objects.all() if is_administrator(request.user) or is_admin_produksi(request.user) else Toko.objects.filter(pk=getattr(toko_user, "pk", None))
    dapur_options = Dapur.objects.all()
    jadwal_options = Jadwal.objects.all()

    if request.method == "POST":
        action = request.POST.get("action")
        if action not in ("draft", "send"):
            messages.error(request, "Aksi transaksi tidak dikenal.")
            return redirect("ro_transaksi")

        toko_id = request.POST.get("toko")
        dapur_id = request.POST.get("dapur")
        jadwal_id = request.POST.get("jadwal")
        tgl_ro = parse_date(request.POST.get("tgl_ro", ""))
        tgl_kirim = parse_date(request.POST.get("tgl_kirim", ""))

        if is_admin_toko(request.user) and not is_administrator(request.user):
            if not toko_user:
                return HttpResponseForbidden("Akun Admin Toko belum dihubungkan ke Kode Toko oleh Administrator.")
            toko_id = str(toko_user.pk)

        try:
            toko = get_object_or_404(toko_options, pk=toko_id)
            dapur = get_object_or_404(Dapur, pk=dapur_id)
            jadwal = get_object_or_404(Jadwal, pk=jadwal_id)
            if not tgl_ro or not tgl_kirim:
                raise ValidationError("Tanggal RO dan Tanggal Kirim wajib diisi.")

            with transaction.atomic():
                existing = RO.objects.select_for_update().filter(
                    tgl_ro=tgl_ro, toko=toko, dapur=dapur, jadwal=jadwal
                )
                if existing.filter(status_ro=RO.STATUS_SENT).exists():
                    raise ValidationError("RO ini sudah Terkirim dan tidak dapat diubah.")

                if existing.exists():
                    items = list(existing.select_related("produk"))
                else:
                    templates = list(TemplateProduk.objects.filter(dapur=dapur).order_by("kode_produk"))
                    if not templates:
                        raise ValidationError("Belum ada Template Produk untuk Dapur yang dipilih.")
                    items = [
                        RO(
                            toko=toko, tgl_ro=tgl_ro, tgl_kirim=tgl_kirim,
                            dapur=dapur, jadwal=jadwal, produk=product,
                            qty_pesan=0, status_ro=RO.STATUS_DRAFT,
                            dibuat_oleh=request.user,
                        )
                        for product in templates
                    ]
                    RO.objects.bulk_create(items)

                if existing.exists() and any(item.tgl_kirim != tgl_kirim for item in items):
                    for item in items:
                        item.tgl_kirim = tgl_kirim

                for item in items:
                    raw_qty = request.POST.get(f"qty_{item.produk_id}", "0").strip()
                    if raw_qty == "":
                        raw_qty = "0"
                    if not raw_qty.isdigit():
                        raise ValidationError(f"Qty produk {item.produk.nama_produk} harus berupa bilangan bulat 0 atau lebih.")
                    item.qty_pesan = int(raw_qty)
                    item.tgl_kirim = tgl_kirim
                    item.status_ro = RO.STATUS_DRAFT if action == "draft" else RO.STATUS_SENT
                    item.save(update_fields=["qty_pesan", "tgl_kirim", "status_ro", "diubah_pada"])

                if action == "send":
                    RO.objects.filter(
                        tgl_ro=tgl_ro, toko=toko, dapur=dapur, jadwal=jadwal,
                        qty_pesan__lt=1, status_ro=RO.STATUS_SENT,
                    ).delete()
                    if not RO.objects.filter(
                        tgl_ro=tgl_ro, toko=toko, dapur=dapur, jadwal=jadwal,
                        status_ro=RO.STATUS_SENT,
                    ).exists():
                        raise ValidationError("Tidak ada Qty minimal 1. Isi setidaknya satu Qty sebelum mengirim RO.")

            messages.success(request, "RO berhasil disimpan sebagai Draft." if action == "draft" else "RO berhasil dikirim dan dikunci.")
            return redirect("ro_daftar")

        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect("ro_transaksi")

    context = {
        "toko_options": toko_options,
        "dapur_options": dapur_options,
        "jadwal_options": jadwal_options,
        "toko_user": toko_user,
        "is_store_operator": is_admin_toko(request.user) and not is_administrator(request.user),
        "today": date.today().isoformat(),
    }
    return render(request, "masterdata/ro_transaksi.html", context)


@login_required
def ro_daftar(request):
    if not can_access_ro(request.user):
        return HttpResponseForbidden("Akun Anda tidak memiliki akses transaksi RO.")
    rows = _ro_queryset(request.user)
    return render(request, "masterdata/ro_daftar.html", {
        "rows": rows,
        "is_admin_produksi": is_admin_produksi(request.user) or is_administrator(request.user),
        "is_administrator": is_administrator(request.user),
    })


@login_required
def ro_edit(request, tgl_ro, toko_id, dapur_id, jadwal_id):
    if not can_access_ro(request.user):
        return HttpResponseForbidden("Akun Anda tidak memiliki akses transaksi RO.")
    key = dict(tgl_ro=tgl_ro, toko_id=toko_id, dapur_id=dapur_id, jadwal_id=jadwal_id)
    rows = _ro_queryset(request.user).filter(**key)
    first = rows.first()
    if not first:
        return redirect("ro_daftar")
    if first.status_ro == RO.STATUS_SENT:
        messages.info(request, "RO berstatus Terkirim dan hanya dapat dilihat.")
        return redirect("ro_daftar")
    if request.method == "GET":
        return render(request, "masterdata/ro_edit.html", {
            "rows": rows.select_related("produk"),
            "first": first,
            "read_only": not (is_admin_toko(request.user) or is_administrator(request.user)),
        })
    return redirect("ro_daftar")
