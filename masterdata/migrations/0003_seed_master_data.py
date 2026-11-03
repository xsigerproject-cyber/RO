from django.db import migrations


def seed_master_data(apps, schema_editor):
    Dapur = apps.get_model("masterdata", "Dapur")
    Jadwal = apps.get_model("masterdata", "Jadwal")
    Toko = apps.get_model("masterdata", "Toko")
    TemplateProduk = apps.get_model("masterdata", "TemplateProduk")
    db_alias = schema_editor.connection.alias

    dapur_data = [
        (10, "Dapur Cake", "Order Cake", "CAKE"),
        (12, "Dapur Cake Slice", "Order Cake Slice", "CAKESL"),
        (13, "Dapur Pastry", "Order Pastry", "PASTRY"),
        (14, "Dapur Jajan Pasar", "Order Jajan Pasar", "JJP"),
        (15, "Dapur Roti", "Order Roti", "ROTI"),
        (16, "Dapur Sultan", "Order Sultan", "SUL"),
    ]

    for kode, nama, operation_type, document in dapur_data:
        Dapur.objects.using(db_alias).update_or_create(
            kode_dapur=kode,
            defaults={
                "nama_dapur": nama,
                "operation_type": operation_type,
                "document": document,
            },
        )

    jadwal_data = [
        (10, "Pagi - Subuh"),
        (12, "Pagi - 10.00 WIB"),
        (13, "Siang - 13.00 WIB"),
    ]

    for kode, jadwal_kirim in jadwal_data:
        Jadwal.objects.using(db_alias).update_or_create(
            kode_jadwal=kode,
            defaults={"jadwal_kirim": jadwal_kirim},
        )

    toko_data = [
        (10, "Toko Sudirman"),
        (12, "Toko Kedaton"),
        (13, "Toko Unila"),
        (14, "Toko RSAM"),
        (15, "Toko Metro"),
        (16, "Toko RS Airan"),
    ]

    for kode, nama in toko_data:
        Toko.objects.using(db_alias).update_or_create(
            kode_toko=kode,
            defaults={"nama_toko": nama},
        )

    produk_data = [
        (10001, "Roti Manis", 15),
        (10002, "Roti Coklat", 15),
        (10003, "Roti Kelapa", 15),
        (10004, "Roti Kopi", 15),
        (10005, "Arem Arem Sultan", 14),
        (10006, "Sosis Solo", 14),
    ]

    for kode_produk, nama_produk, kode_dapur in produk_data:
        dapur = Dapur.objects.using(db_alias).get(kode_dapur=kode_dapur)
        TemplateProduk.objects.using(db_alias).update_or_create(
            kode_produk=kode_produk,
            defaults={
                "nama_produk": nama_produk,
                "dapur_id": dapur.pk,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("masterdata", "0002_userprofile"),
    ]

    operations = [
        migrations.RunPython(seed_master_data, migrations.RunPython.noop),
    ]
