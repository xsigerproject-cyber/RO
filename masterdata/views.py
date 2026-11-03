import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    Http404,
    JsonResponse,
)
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q, CharField, TextField, IntegerField
from django.core.exceptions import FieldDoesNotExist
from openpyxl import Workbook, load_workbook

from .models import Dapur, Jadwal, Toko, TemplateProduk, UserProfile
from .forms import (
    DapurForm,
    JadwalForm,
    TokoForm,
    TemplateProdukForm,
)
from .permissions import can_manage, can_delete, is_admin_toko


logger = logging.getLogger(__name__)
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


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
        ["kode_produk", "nama_produk", "dapur", "is_active"],
        "Template Produk",
    ),
}


def cfg(kind):
    if kind not in CONFIG:
        raise Http404("Master data tidak ditemukan.")

    return CONFIG[kind]


@login_required
@require_POST
def set_theme(request):
    theme = request.POST.get("theme", "light")
    valid_themes = [choice[0] for choice in UserProfile.THEME_CHOICES]

    if theme not in valid_themes:
        return JsonResponse(
            {"status": "error", "message": "Tema tidak valid"},
            status=400,
        )

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.theme = theme
    profile.save(update_fields=["theme"])

    return JsonResponse({"status": "success", "theme": theme})


@login_required
def dashboard(request):
    if is_admin_toko(request.user) and not request.user.is_superuser:
        return redirect("ro_transaksi")

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
    if is_admin_toko(request.user) and not request.user.is_superuser:
        return HttpResponseForbidden("Admin Toko hanya dapat mengakses transaksi untuk tokonya.")

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
    if is_admin_toko(request.user) and not request.user.is_superuser:
        return HttpResponseForbidden("Admin Toko tidak memiliki akses ekspor master data.")

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
def download_import_template(request, kind):
    if not can_manage(request.user):
        return HttpResponseForbidden(
            "Anda tidak memiliki izin mengimpor data."
        )

    model, _, fields, title = cfg(kind)

    wb = Workbook()
    ws = wb.active
    ws.title = "Template Import"

    headers = [
        "kode_dapur" if field_name == "dapur" else field_name
        for field_name in fields
    ]
    ws.append(headers)

    # Gunakan record pertama dari tabel sebagai baris contoh.
    # Urutan mengikuti primary key terkecil agar hasil konsisten.
    sample_obj = model.objects.order_by(model._meta.pk.name).first()
    if sample_obj is not None:
        sample_row = []
        for field_name in fields:
            if field_name == "dapur":
                value = sample_obj.dapur_id
            else:
                value = getattr(sample_obj, field_name, "")
            sample_row.append(value if value is not None else "")
        ws.append(sample_row)

    # Format header dan baris contoh jika tersedia.
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.comments import Comment

    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="0D6EFD",
        )
        cell.alignment = Alignment(horizontal="center")

    for column_cells in ws.columns:
        column_letter = column_cells[0].column_letter
        header_length = len(str(column_cells[0].value or ""))
        sample_length = max(
            (len(str(cell.value or "")) for cell in column_cells[1:]),
            default=0,
        )
        ws.column_dimensions[column_letter].width = max(
            18, min(max(header_length, sample_length) + 5, 40)
        )

    if sample_obj is not None:
        for cell in ws[2]:
            cell.font = Font(italic=True, color="666666")
            cell.fill = PatternFill(fill_type="solid", fgColor="FFF2CC")
            cell.alignment = Alignment(vertical="center")
            cell.comment = Comment(
                "BARIS CONTOH: diambil dari record pertama pada tabel. "
                "Boleh diubah atau dihapus sebelum import. Jika diimpor "
                "tanpa perubahan, data dengan kode yang sama akan diperbarui, "
                "bukan dibuat sebagai duplikat.",
                "RO",
            )

    ws.freeze_panes = "A2"
    last_row = 2 if sample_obj is not None else 1
    ws.auto_filter.ref = (
        f"A1:{ws.cell(row=last_row, column=len(headers)).coordinate}"
    )

    if kind == "produk":
        dapur_column = headers.index("kode_dapur") + 1
        ws.cell(row=1, column=dapur_column).comment = Comment(
            "Nilai berisi kode_dapur yang terhubung dengan produk contoh.",
            "RO",
        )

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )
    response["Content-Disposition"] = (
        f'attachment; filename="template_import_{kind}.xlsx"'
    )
    wb.save(response)
    return response


@login_required
@require_POST
def import_excel(request, kind):
    if not can_manage(request.user):
        return HttpResponseForbidden(
            "Anda tidak memiliki izin mengimpor data."
        )

    model, FormClass, fields, title = cfg(kind)
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        messages.error(
            request,
            "Silakan pilih berkas Excel terlebih dahulu.",
        )
        return redirect("master_list", kind)

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        messages.error(
            request,
            "Ukuran berkas maksimal 5 MB.",
        )
        return redirect("master_list", kind)

    if not uploaded_file.name.lower().endswith(".xlsx"):
        messages.error(
            request,
            "Format berkas harus Excel .xlsx.",
        )
        return redirect("master_list", kind)

    wb = None

    try:
        wb = load_workbook(
            uploaded_file,
            data_only=True,
            read_only=True,
        )
        ws = wb.active

        first_row = next(
            ws.iter_rows(
                min_row=1,
                max_row=1,
                values_only=True,
            ),
            None,
        )

        if not first_row:
            raise ValidationError("Berkas Excel kosong.")

        headers = [
            str(value).strip().lower() if value is not None else ""
            for value in first_row
        ]

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
            raise ValidationError(
                "Kolom Excel tidak lengkap: "
                + ", ".join(missing_headers)
            )

        def parse_integer(value, label, row_number):
            if isinstance(value, bool):
                raise ValidationError(
                    f"{label} tidak valid pada baris {row_number}."
                )

            if isinstance(value, int):
                return value

            if isinstance(value, float) and value.is_integer():
                return int(value)

            text_value = str(value).strip() if value is not None else ""
            if text_value.isdigit():
                return int(text_value)

            raise ValidationError(
                f"{label} harus berupa angka bulat pada baris {row_number}."
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

                pk_value = row_data.get(pk_field)
                if (
                    isinstance(pk_value, str)
                    and pk_value.strip().upper() == "__CONTOH__"
                ):
                    continue

                row_data[pk_field] = parse_integer(
                    pk_value,
                    f"Primary key {pk_field}",
                    row_number,
                )

                if kind == "produk":
                    dapur_code = row_data.pop("kode_dapur", None)
                    row_data["dapur"] = parse_integer(
                        dapur_code,
                        "Kode dapur",
                        row_number,
                    )

                for field_name in fields:
                    if field_name == "dapur":
                        continue
                    value = row_data.get(field_name)
                    if isinstance(value, str):
                        row_data[field_name] = value.strip()

                instance = model.objects.filter(
                    pk=row_data[pk_field]
                ).first()

                form = FormClass(
                    data=row_data,
                    instance=instance,
                )

                if not form.is_valid():
                    raise ValidationError(
                        f"Kesalahan pada baris {row_number}: "
                        f"{form.errors.as_text()}"
                    )

                form.save()
                imported_count += 1

        messages.success(
            request,
            (
                f"Impor Excel {title} berhasil. "
                f"{imported_count} baris berhasil diproses."
            ),
        )

    except ValidationError as error:
        messages.error(
            request,
            f"Gagal mengimpor Excel: {error}",
        )
    except Exception:
        logger.exception(
            "Terjadi kesalahan saat mengimpor Excel untuk master %s.",
            kind,
        )
        messages.error(
            request,
            "Terjadi kesalahan saat memproses berkas Excel. "
            "Periksa format berkas atau hubungi administrator.",
        )
    finally:
        if wb is not None:
            wb.close()

    return redirect("master_list", kind)
