# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SanPham, DanhMucSanPham, DonViTinh  # ← Import model
from .forms import SanPhamForm, DanhMucForm, DonViTinhForm

@login_required
def product_list(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        form = SanPhamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = SanPhamForm()
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Thêm sản phẩm'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(SanPham, pk=pk)
    if request.method == 'POST':
        form = SanPhamForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = SanPhamForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Chỉnh sửa sản phẩm'})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(SanPham, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})


@login_required
def category_list(request):
    categories = DanhMucSanPham.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})

@login_required
def unit_list(request):
    units = DonViTinh.objects.all()
    return render(request, 'products/unit_list.html', {'units': units})


@login_required
def category_create(request):
    if request.method == 'POST':
        form = DanhMucForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = DanhMucForm()

    return render(request, 'products/category_form.html', {
        'form': form,
        'title': 'Thêm danh mục mới'
    })


@login_required
def unit_create(request):
    if request.method == 'POST':
        form = DonViTinhForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('unit_list')
    else:
        form = DonViTinhForm()

    return render(request, 'products/unit_form.html', {
        'form': form,
        'title': 'Thêm đơn vị tính'
    })