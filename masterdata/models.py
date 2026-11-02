from django.db import models
class Dapur(models.Model):
    kode_dapur = models.PositiveIntegerField(primary_key=True)
    nama_dapur = models.CharField(max_length=120)
    operation_type = models.CharField(max_length=120)
    document = models.CharField(max_length=60)
    class Meta: ordering = ["kode_dapur"]
    def __str__(self): return f"{self.kode_dapur} - {self.nama_dapur}"
class Jadwal(models.Model):
    kode_jadwal = models.PositiveIntegerField(primary_key=True)
    jadwal_kirim = models.CharField(max_length=120)
    class Meta: ordering = ["kode_jadwal"]
    def __str__(self): return self.jadwal_kirim
class Toko(models.Model):
    kode_toko = models.PositiveIntegerField(primary_key=True)
    nama_toko = models.CharField(max_length=120)
    class Meta: ordering = ["kode_toko"]
    def __str__(self): return self.nama_toko
class TemplateProduk(models.Model):
    kode_produk = models.PositiveIntegerField(primary_key=True)
    nama_produk = models.CharField(max_length=160)
    dapur = models.ForeignKey(Dapur, on_delete=models.PROTECT, related_name="produk")
    class Meta: ordering = ["kode_produk"]
    def __str__(self): return self.nama_produk
