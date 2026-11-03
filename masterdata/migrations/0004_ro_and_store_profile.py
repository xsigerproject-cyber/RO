from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0003_seed_master_data"),
        migrations.swappable_dependency("auth.User"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="toko",
            field=models.ForeignKey(
                blank=True,
                help_text="Wajib diisi untuk akun dengan role Admin Toko.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="admin_users",
                to="masterdata.toko",
            ),
        ),
        migrations.CreateModel(
            name="RO",
            fields=[
                ("id_ro", models.BigAutoField(primary_key=True, serialize=False)),
                ("tgl_ro", models.DateField()),
                ("tgl_produksi", models.DateField(blank=True, null=True)),
                ("tgl_kirim", models.DateField()),
                ("qty_pesan", models.PositiveIntegerField(default=0)),
                ("status_ro", models.PositiveSmallIntegerField(choices=[(1, "Draft"), (2, "Terkirim")], default=1)),
                ("dibuat_pada", models.DateTimeField(auto_now_add=True)),
                ("diubah_pada", models.DateTimeField(auto_now=True)),
                ("dapur", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ro_items", to="masterdata.dapur")),
                ("dibuat_oleh", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ro_dibuat", to="auth.user")),
                ("jadwal", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ro_items", to="masterdata.jadwal")),
                ("produk", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ro_items", to="masterdata.templateproduk")),
                ("toko", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ro_items", to="masterdata.toko")),
            ],
            options={"ordering": ["produk__kode_produk"]},
        ),
        migrations.AddConstraint(
            model_name="ro",
            constraint=models.UniqueConstraint(fields=("tgl_ro", "toko", "dapur", "jadwal", "produk"), name="uniq_ro_date_store_kitchen_schedule_product"),
        ),
        migrations.AddIndex(
            model_name="ro",
            index=models.Index(fields=["tgl_ro", "toko", "dapur", "jadwal"], name="masterdata_ro_tgl_ro_51f4f0_idx"),
        ),
        migrations.AddIndex(
            model_name="ro",
            index=models.Index(fields=["status_ro", "tgl_kirim"], name="masterdata_ro_status_12a7bf_idx"),
        ),
    ]
