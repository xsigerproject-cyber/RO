from django import forms
from .models import Dapur, Jadwal, Toko, TemplateProduk
class BootstrapForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values(): field.widget.attrs["class"]="form-control"
class DapurForm(BootstrapForm):
    class Meta: model=Dapur; fields="__all__"
class JadwalForm(BootstrapForm):
    class Meta: model=Jadwal; fields="__all__"
class TokoForm(BootstrapForm):
    class Meta: model=Toko; fields="__all__"
class TemplateProdukForm(BootstrapForm):
    class Meta: model=TemplateProduk; fields="__all__"
