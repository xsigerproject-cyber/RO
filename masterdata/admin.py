from django.contrib import admin
from .models import Dapur, Jadwal, Toko, TemplateProduk
admin.site.register([Dapur, Jadwal, Toko, TemplateProduk])
