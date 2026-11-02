from django.core.management.base import BaseCommand
from masterdata.models import Dapur,Jadwal,Toko,TemplateProduk
from django.contrib.auth.models import Group
class Command(BaseCommand):
    help="Isi data master awal dan grup role"
    def handle(self,*args,**kwargs):
        dapurs=[(10,"Dapur Cake","Order Cake","CAKE"),(12,"Dapur Cake Slice","Order Cake Slice","CAKESL"),(13,"Dapur Pastry","Order Pastry","PASTRY"),(14,"Dapur Jajan Pasar","Order Jajan Pasar","JJP"),(15,"Dapur Roti","Order Roti","ROTI"),(16,"Dapur Sultan","Order Sultan","SUL")]
        for k,n,o,d in dapurs: Dapur.objects.update_or_create(kode_dapur=k,defaults={"nama_dapur":n,"operation_type":o,"document":d})
        for k,n in [(10,"Pagi - Subuh"),(12,"Pagi - 10.00 WIB"),(13,"Siang - 13.00 WIB")]: Jadwal.objects.update_or_create(kode_jadwal=k,defaults={"jadwal_kirim":n})
        for k,n in [(10,"Toko Sudirman"),(12,"Toko Kedaton"),(13,"Toko Unila"),(14,"Toko RSAM"),(15,"Toko Metro"),(16,"Toko RS Airan")]: Toko.objects.update_or_create(kode_toko=k,defaults={"nama_toko":n})
        for k,n,d in [(10001,"Roti Manis",15),(10002,"Roti Coklat",15),(10003,"Roti Kelapa",15),(10004,"Roti Kopi",15),(10005,"Arem Arem Sultan",14),(10006,"Sosis Solo",14)]: TemplateProduk.objects.update_or_create(kode_produk=k,defaults={"nama_produk":n,"dapur_id":d})
        for name in ["Admin Master","Editor Master","Viewer Master"]: Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Data master dan grup role berhasil disiapkan."))
