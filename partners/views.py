from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import NhaCungCap
from .forms import NhaCungCapForm

@login_required
def supplier_list(request):
    suppliers = NhaCungCap.objects.all()
    return render(request, 'partners/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = NhaCungCapForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm nhà cung cấp thành công!')
            return redirect('supplier_list')
    else:
        form = NhaCungCapForm()
    return render(request, 'partners/supplier_form.html', {'form': form, 'title': 'Thêm nhà cung cấp'})

