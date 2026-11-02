from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Dapur', fields=[('kode_dapur',models.PositiveIntegerField(primary_key=True,serialize=False)),('nama_dapur',models.CharField(max_length=120)),('operation_type',models.CharField(max_length=120)),('document',models.CharField(max_length=60))], options={'ordering':['kode_dapur']}),
        migrations.CreateModel(name='Jadwal', fields=[('kode_jadwal',models.PositiveIntegerField(primary_key=True,serialize=False)),('jadwal_kirim',models.CharField(max_length=120))], options={'ordering':['kode_jadwal']}),
        migrations.CreateModel(name='Toko', fields=[('kode_toko',models.PositiveIntegerField(primary_key=True,serialize=False)),('nama_toko',models.CharField(max_length=120))], options={'ordering':['kode_toko']}),
        migrations.CreateModel(name='TemplateProduk', fields=[('kode_produk',models.PositiveIntegerField(primary_key=True,serialize=False)),('nama_produk',models.CharField(max_length=160)),('dapur',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='produk',to='masterdata.dapur'))], options={'ordering':['kode_produk']}),
    ]
