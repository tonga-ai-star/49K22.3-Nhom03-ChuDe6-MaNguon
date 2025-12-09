from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile
from .forms import (
    UserEditForm,
    ProfileEditForm,
    StaffCreateForm,
    StaffEditForm
)

# 1️. Hồ sơ người dùng (Profile)
@login_required
def profile_view(request):
    user = request.user
    Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        uform = UserEditForm(request.POST, instance=user)
        pform = ProfileEditForm(request.POST, request.FILES, instance=user.profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "Cập nhật hồ sơ thành công.")
            return redirect('settings:profile')
    else:
        uform = UserEditForm(instance=user)
        pform = ProfileEditForm(instance=user.profile)

    return render(request, 'settings_app/profile.html', {'uform': uform, 'pform': pform})

# 2️.Đăng xuất
@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login')

# 3️. Quản lý nhân viên (Admin)
def is_admin(user):
    return user.is_superuser or user.is_staff

@user_passes_test(is_admin)
def staff_list(request):
    staffs = User.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'settings_app/staff_list.html', {'staffs': staffs})

@user_passes_test(is_admin)
def staff_create(request):
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tạo tài khoản nhân viên thành công.")
            return redirect('settings:staff_list')
    else:
        form = StaffCreateForm()
    return render(request, 'settings_app/staff_form.html', {'form': form, 'create': True})

@user_passes_test(is_admin)
def staff_edit(request, pk):
    staff = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật tài khoản thành công.")
            return redirect('settings:staff_list')
    else:
        form = StaffEditForm(instance=staff)
    return render(request, 'settings_app/staff_form.html', {'form': form, 'create': False})

@user_passes_test(is_admin)
def staff_delete(request, pk):
    staff = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, "Xóa tài khoản thành công.")
        return redirect('settings:staff_list')
    return render(request, 'settings_app/staff_confirm_delete.html', {'staff': staff})

@login_required
def profile_detail(request):
    user = request.user
    profile = user.profile
    return render(request, 'settings_app/profile_detail.html', {
        'user': user,
        'profile': profile
    })
from django.shortcuts import render

# Create your views here.
