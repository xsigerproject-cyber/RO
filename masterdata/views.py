from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    Http404,
)
from django.db import transaction
from django.db.models import Q, CharField, TextField, IntegerField
from django.core.exceptions import FieldDoesNotExist
from openpyxl import Workbook, load_workbook

from .models import Dapur, Jadwal, Toko, TemplateProduk
from .forms import (
    DapurForm,
    JadwalForm,
    TokoForm,
    TemplateProdukForm,
)
from .permissions import can_manage, can_delete


CONFIG = {
    "dapur": (
        Dapur,
        DapurForm,
        ["kode_dapur", "nama_dapur", "operation_type", "document"],
        "Dapur",
    ),
    "jadwal": (
        Jadwal,
        JadwalForm,
        ["kode_jadwal", "jadwal_kirim"],
        "Jadwal",
    ),
    "toko": (
        Toko,
        TokoForm,
        ["kode_toko", "nama_toko"],
        "Toko",
    ),
    "produk": (
        TemplateProduk,
        TemplateProdukForm,
        ["kode_produk", "nama_produk", "dapur"],
        "Template Produk",
    ),
}


def cfg(kind):
    if kind not in CONFIG:
        raise Http404("Master data tidak ditemukan.")

    return CONFIG[kind]


@login_required
def dashboard(request):
    counts = {
        "dapur": Dapur.objects.count(),
        "jadwal": Jadwal.objects.count(),
        "toko": Toko.objects.count(),
        "produk": TemplateProduk.objects.count(),
    }

    return render(
        request,
        "masterdata/dashboard.html",
        {"counts": counts},
    )


@login_required
def list_data(request, kind):
    model, form_class, fields, title = cfg(kind)

    q = request.GET.get("q", "").strip()
    qs = model.objects.all()

    if q:
        condition = Q()

        for field_name in fields:
            if field_name == "dapur":
                condition |= (
                    Q(dapur__nama_dapur__icontains=q)
                    | Q(dapur__kode_dapur__icontains=q)
                )
                continue

            try:
                field_obj = model._meta.get_field(field_name)

                if isinstance(field_obj, (CharField, TextField)):
                    condition |= Q(
                        **{f"{field_name}__icontains": q}
                    )

                elif (
                    isinstance(field_obj, IntegerField)
                    and q.isdigit()
                ):
                    condition |= Q(**{field_name: int(q)})

            except FieldDoesNotExist:
                continue

        qs = qs.filter(condition)

    return render(
        request,
        "masterdata/list.html",
        {
            "kind": kind,
            "title": title,
            "fields": fields,
            "objects": qs,
            "create_form": form_class() if can_manage(request.user) else None,
            "show_create_modal": False,
            "can_manage": can_manage(request.user),
            "can_delete": can_delete(request.user),
        },
    )


@login_required
def edit_data(request, kind, pk=None):
    if not can_manage(request.user):
        return HttpResponseForbidden(
            "Anda tidak memiliki izin mengelola data."
        )

    model, FormClass, fields, title = cfg(kind)

    obj = get_object_or_404(model, pk=pk) if pk else None

    form_data = request.POST if request.method == "POST" else None

    form = FormClass(form_data, instance=obj)

    if request.method == "POST":
        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"Data {title} berhasil disimpan.",
            )

            return redirect("master_list", kind)

        messages.error(
            request,
            "Gagal menyimpan data. Periksa kembali isian form.",
        )

    if pk:
        return render(
            request,
            "masterdata/form.html",
            {
                "form": form,
                "title": title,
                "kind": kind,
            },
        )

    # Jika validasi tambah data gagal, tampilkan kembali daftar
    # dengan modal tetap terbuka dan pesan error pada field.
    return render(
        request,
        "masterdata/list.html",
        {
            "kind": kind,
            "title": title,
            "fields": fields,
            "objects": model.objects.all(),
            "create_form": form,
            "show_create_modal": True,
            "can_manage": can_manage(request.user),
            "can_delete": can_delete(request.user),
        },
    )


@login_required
def delete_data(request, kind, pk):
    if not can_delete(request.user):
        return HttpResponseForbidden(
            "Anda tidak memiliki izin menghapus data."
        )

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    model, _, _, title = cfg(kind)

    obj = get_object_or_404(model, pk=pk)
    obj.delete()

    messages.success(
        request,
        f"Data {title} berhasil dihapus.",
    )

    return redirect("master_list", kind)


@login_required
def export_excel(request, kind):
    model, _, fields, title = cfg(kind)

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]

    # Header Excel
    headers = [
        "kode_dapur" if field_name == "dapur" else field_name
        for field_name in fields
    ]

    ws.append(headers)

    # Isi data Excel
    for obj in model.objects.all():
        row = []

        for field_name in fields:
            if field_name == "dapur":
                value = obj.dapur_id
            else:
                value = getattr(obj, field_name, "")

            row.append(value if value is not None else "")

        ws.append(row)

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{kind}.xlsx"'
    )

    wb.save(response)

    return response


@login_required
def import_excel(request, kind):
    if not can_manage(request.user):
        return HttpResponseForbidden(
            "Anda tidak memiliki izin mengimpor data."
        )

    model, FormClass, fields, title = cfg(kind)

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        messages.error(
            request,
            "Silakan pilih berkas Excel terlebih dahulu.",
        )
        return redirect("master_list", kind)

    if not uploaded_file.name.lower().endswith(".xlsx"):
        messages.error(
            request,
            "Format berkas harus Excel .xlsx.",
        )
        return redirect("master_list", kind)

    try:
        wb = load_workbook(
            uploaded_file,
            data_only=True,
            read_only=True,
        )

        ws = wb.active

        # Membaca header Excel
        first_row = next(
            ws.iter_rows(
                min_row=1,
                max_row=1,
                values_only=True,
            ),
            None,
        )

        if not first_row:
            raise ValueError("Berkas Excel kosong.")

        headers = [
            str(value).strip().lower() if value is not None else ""
            for value in first_row
        ]

        # Header yang wajib tersedia
        required_headers = [
            "kode_dapur" if field_name == "dapur" else field_name
            for field_name in fields
        ]

        missing_headers = [
            header
            for header in required_headers
            if header not in headers
        ]

        if missing_headers:
            raise ValueError(
                "Kolom Excel tidak lengkap: "
                + ", ".join(missing_headers)
            )

        pk_field = model._meta.pk.name
        imported_count = 0

        with transaction.atomic():

            for row_number, row in enumerate(
                ws.iter_rows(
                    min_row=2,
                    values_only=True,
                ),
                start=2,
            ):

                # Abaikan baris yang benar-benar kosong
                if not row or all(
                    value is None or str(value).strip() == ""
                    for value in row
                ):
                    continue

                row_data = {
                    header: value
                    for header, value in zip(headers, row)
                    if header
                }

                # Primary key wajib tersedia
                pk_value = row_data.get(pk_field)

                if pk_value is None or str(pk_value).strip() == "":
                    raise ValueError(
                        f"Primary key {pk_field} kosong "
                        f"pada baris {row_number}."
                    )

                # Konversi kode_dapur menjadi field relasi dapur
                if kind == "produk":
                    dapur_code = row_data.pop(
                        "kode_dapur",
                        None,
                    )

                    if dapur_code is None or str(dapur_code).strip() == "":
                        raise ValueError(
                            f"Kode dapur kosong pada baris {row_number}."
                        )

                    row_data["dapur"] = dapur_code

                # Cari data lama berdasarkan primary key
                instance = model.objects.filter(
                    pk=pk_value
                ).first()

                # Validasi menggunakan ModelForm
                form = FormClass(
                    data=row_data,
                    instance=instance,
                )

                if not form.is_valid():
                    raise ValueError(
                        f"Kesalahan pada baris {row_number}: "
                        f"{form.errors.as_text()}"
                    )

                # Jika data belum ada, Django membuat data baru.
                # Jika sudah ada, Django memperbarui data tersebut.
                form.save()

                imported_count += 1

        wb.close()

        messages.success(
            request,
            (
                f"Impor Excel {title} berhasil. "
                f"{imported_count} baris berhasil diproses."
            ),
        )

    except Exception as error:
        messages.error(
            request,
            f"Gagal mengimpor Excel: {str(error)}",
        )

    return redirect("master_list", kind)
