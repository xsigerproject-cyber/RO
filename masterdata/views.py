from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.db import transaction
from openpyxl import Workbook, load_workbook
from .models import Dapur, Jadwal, Toko, TemplateProduk
from .forms import DapurForm, JadwalForm, TokoForm, TemplateProdukForm
from .permissions import can_manage, can_delete
CONFIG = {
 "dapur": (Dapur,DapurForm,["kode_dapur","nama_dapur","operation_type","document"],"Dapur"),
 "jadwal": (Jadwal,JadwalForm,["kode_jadwal","jadwal_kirim"],"Jadwal"),
 "toko": (Toko,TokoForm,["kode_toko","nama_toko"],"Toko"),
 "produk": (TemplateProduk,TemplateProdukForm,["kode_produk","nama_produk","dapur"],"Template Produk"),
}
def cfg(kind):
    if kind not in CONFIG: raise ValueError("Master tidak dikenal")
    return CONFIG[kind]
@login_required
def dashboard(request):
    return render(request,"masterdata/dashboard.html",{"counts":{"dapur":Dapur.objects.count(),"jadwal":Jadwal.objects.count(),"toko":Toko.objects.count(),"produk":TemplateProduk.objects.count()}})
@login_required
def list_data(request,kind):
    model,form,fields,title=cfg(kind); q=request.GET.get("q","")
    qs=model.objects.all()
    if q:
        from django.db.models import Q
        condition=Q()
        for f in fields:
            if f!="dapur": condition |= Q(**{f+"__icontains":q})
        qs=qs.filter(condition)
    return render(request,"masterdata/list.html",{"kind":kind,"title":title,"fields":fields,"objects":qs,"can_manage":can_manage(request.user),"can_delete":can_delete(request.user)})
@login_required
def edit_data(request,kind,pk=None):
    if not can_manage(request.user): return HttpResponseForbidden()
    model,Form,fields,title=cfg(kind); obj=get_object_or_404(model,pk=pk) if pk else None
    form=Form(request.POST or None,instance=obj)
    if request.method=="POST" and form.is_valid(): form.save(); messages.success(request,"Data berhasil disimpan."); return redirect("master_list",kind)
    return render(request,"masterdata/form.html",{"form":form,"title":title,"kind":kind})
@login_required
def delete_data(request,kind,pk):
    if not can_delete(request.user): return HttpResponseForbidden()
    model,*_=cfg(kind)
    if request.method=="POST": get_object_or_404(model,pk=pk).delete(); messages.success(request,"Data dihapus.")
    return redirect("master_list",kind)
@login_required
def export_excel(request,kind):
    model,_,fields,title=cfg(kind); wb=Workbook(); ws=wb.active; ws.title=title[:31]
    headers=[("kode_dapur" if f=="dapur" else f) for f in fields]; ws.append(headers)
    for obj in model.objects.all():
        ws.append([getattr(obj,"dapur_id") if f=="dapur" else getattr(obj,f) for f in fields])
    response=HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"]=f'attachment; filename="{kind}.xlsx"'; wb.save(response); return response
@login_required
def import_excel(request,kind):
    if not can_manage(request.user): return HttpResponseForbidden()
    model,_,fields,title=cfg(kind)
    if request.method=="POST" and request.FILES.get("file"):
        wb=load_workbook(request.FILES["file"],data_only=True); ws=wb.active
        headers=[str(c.value).strip().lower() for c in ws[1]]
        with transaction.atomic():
            for row in ws.iter_rows(min_row=2,values_only=True):
                data=dict(zip(headers,row))
                if kind=="produk":
                    data["dapur_id"]=data.pop("kode_dapur")
                model.objects.update_or_create(**{model._meta.pk.name:data[model._meta.pk.name]},defaults={k:v for k,v in data.items() if k!=model._meta.pk.name})
        messages.success(request,"Impor Excel selesai.")
    return redirect("master_list",kind)
