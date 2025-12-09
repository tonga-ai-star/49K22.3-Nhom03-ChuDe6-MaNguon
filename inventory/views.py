from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import KiemKe, ChiTietKiemKe
from .models import Kho, TonKho
from products.models import SanPham, DanhMucSanPham, DonViTinh
from .models import NhapKho, ChiTietNhapKho, XuatKho, ChiTietXuatKho
from .forms import NhapKhoForm, ChiTietNhapKhoFormSet, XuatKhoForm, ChiTietXuatKhoFormSet
from .services import QuanLyTonKho
from django.db import transaction
from partners.models import NhaCungCap
from datetime import datetime, timedelta
from debt.models import CongNo
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.db import OperationalError
from django.core.paginator import Paginator
import json

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum
from django.shortcuts import render
from .models import NhapKho


def danh_sach_nhap(request):
    # Lấy tất cả phiếu nhập
    phieu_nhap = NhapKho.objects.select_related('nha_cung_cap', 'nguoi_lap', 'kho').order_by('-ngay_nhap')

    # --- Xử lý bộ lọc ---
    search_query = request.GET.get('q', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Lọc theo ngày
    if start_date:
        phieu_nhap = phieu_nhap.filter(ngay_nhap__gte=start_date)
    if end_date:
        phieu_nhap = phieu_nhap.filter(ngay_nhap__lte=end_date)

    # Tìm kiếm
    if search_query:
        phieu_nhap = phieu_nhap.filter(
            Q(ma_phieu__icontains=search_query) |
            Q(nha_cung_cap__ten_nha_cung_cap__icontains=search_query) |
            Q(nguoi_lap__username__icontains=search_query)
        )

    # --- Phân trang ---
    paginator = Paginator(phieu_nhap, 20)  # 20 item mỗi trang
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    # Tính tổng tiền cho từng phiếu trên trang hiện tại
    total_amount = 0
    for phieu in page_obj:
        # Cách 1: Nếu có trường tong_tien trong model
        if hasattr(phieu, 'tong_tien') and phieu.tong_tien:
            tong_tien = phieu.tong_tien
        else:
            # Cách 2: Tính tổng từ chi tiết
            tong_tien = ChiTietNhapKho.objects.filter(phieu_nhap=phieu).aggregate(
                tong=Sum('thanh_tien')
            )['tong'] or 0
            phieu.tong_tien_calculated = tong_tien

        total_amount += tong_tien

        # Đếm số lượng sản phẩm
        phieu.so_san_pham = phieu.chi_tiet_nhap.count()

    context = {
        'phieu_nhap': page_obj,  # Dùng page_obj thay vì phieu_nhap
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_amount': total_amount,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'inventory/nhapkho_list.html', context)

def generate_ma_ncc():
    """Sinh mã NCC tự động"""
    last = NhaCungCap.objects.order_by('-id').first()
    seq = (last.id + 1) if last else 1
    return f"NCC-{seq:04d}"


@login_required
def nhap_kho_create(request):
    """Tạo phiếu nhập kho với hỗ trợ NCC mới và cập nhật tồn kho"""
    kho_list = Kho.objects.filter(trang_thai='dang_hoat_dong')

    if request.method == 'POST':
        kho_id = request.POST.get('kho_id')
        nha_cung_cap_id = request.POST.get('nha_cung_cap_id')
        nha_cung_cap_moi = request.POST.get('nha_cung_cap_moi', '').strip()
        ghi_chu = request.POST.get('ghi_chu', '').strip()

        try:
            with transaction.atomic():
                # --- 1️ Xử lý nhà cung cấp ---
                if nha_cung_cap_id:
                    nha_cung_cap = get_object_or_404(NhaCungCap, id=nha_cung_cap_id)
                elif nha_cung_cap_moi:
                    nha_cung_cap, _ = NhaCungCap.objects.get_or_create(
                        ten_nha_cung_cap=nha_cung_cap_moi,
                        defaults={'ma_nha_cung_cap': generate_ma_ncc()}
                    )
                else:
                    messages.error(request, "Vui lòng chọn hoặc nhập Nhà cung cấp.")
                    return redirect('inventory:nhap_kho_create')

                # --- 2. Xử lý kho ---
                if kho_id:
                    try:
                        kho_id = int(kho_id)
                        kho = get_object_or_404(Kho, id=kho_id)
                    except (ValueError, TypeError):
                        messages.error(request, "Kho không hợp lệ!")
                        return redirect('inventory:nhap_kho_create')
                else:
                    messages.error(request, "Vui lòng chọn kho!")
                    return redirect('inventory:nhap_kho_create')

                # --- 3️. Tạo phiếu nhập ---
                nhapkho = NhapKho.objects.create(
                    nha_cung_cap=nha_cung_cap,
                    nguoi_lap=request.user,
                    kho=kho,
                    ghi_chu=ghi_chu,
                    ngay_nhap=timezone.now(),
                    tong_tien=0  # Khởi tạo tổng tiền = 0
                )

                # --- 4️. Lưu chi tiết sản phẩm ---
                ten_san_pham_list = request.POST.getlist('ten_san_pham')
                so_luong_list = request.POST.getlist('so_luong')
                don_gia_list = request.POST.getlist('don_gia')

                for i, ten_sp in enumerate(ten_san_pham_list):
                    if not ten_sp.strip():
                        continue
                    try:
                        sp = SanPham.objects.get(ten_san_pham=ten_sp)
                        sl = int(so_luong_list[i])
                        dg = Decimal(don_gia_list[i])
                    except (ValueError, IndexError, SanPham.DoesNotExist):
                        continue

                    if sl <= 0 or dg <= 0:
                        continue

                    # Tạo chi tiết nhập (sẽ tự động cập nhật tong_tien qua save method)
                    ChiTietNhapKho.objects.create(
                        phieu_nhap=nhapkho,
                        san_pham=sp,
                        so_luong=sl,
                        don_gia=dg
                    )


                # Tạo công nợ tự động (sử dụng nhapkho.tong_tien đã được tính)
                tao_cong_no_tu_dong(nhapkho)

                messages.success(request, f"Tạo phiếu nhập {nhapkho.ma_phieu} thành công! Tổng tiền: {nhapkho.tong_tien:,.0f}₫")
                return redirect('inventory:nhapkho_list')

        except Exception as e:
            messages.error(request, f"Lỗi khi nhập kho: {e}")

    # GET request
    context = {
        'form': NhapKhoForm(user=request.user),
        'san_pham_list': SanPham.objects.filter(trang_thai=True),
        'nha_cung_cap_list': NhaCungCap.objects.all(),
        'danh_muc_list': DanhMucSanPham.objects.all(),
        'don_vi_tinh_list': DonViTinh.objects.all(),
        'kho_list': kho_list,
    }
    return render(request, 'inventory/nhapkho_form.html', context)


from django.db.models import Sum


def nhap_kho_detail(request, pk):
    phieu_nhap = get_object_or_404(NhapKho, pk=pk)
    chi_tiet_list = phieu_nhap.chi_tiet_nhap.all()

    tong_tien = chi_tiet_list.aggregate(
        tong=Sum('thanh_tien')
    )['tong'] or Decimal('0')

    return render(request, 'inventory/nhapkho_detail.html', {
        'phieu_nhap': phieu_nhap,
        'chi_tiet_list': chi_tiet_list,
        'tong_tien': tong_tien
    })

def tao_cong_no_tu_dong(nhapkho):
    from datetime import datetime, timedelta
    from debt.models import CongNo
    han_thanh_toan = datetime.now() + timedelta(days=30)
    CongNo.objects.create(
        nha_cung_cap=nhapkho.nha_cung_cap,
        phieu_nhap=nhapkho,
        loai_cong_no='nhap_hang',
        so_tien=nhapkho.tong_tien,
        so_tien_con_lai=nhapkho.tong_tien,
        han_thanh_toan=han_thanh_toan.date(),
        ghi_chu=f"Công nợ từ phiếu nhập {nhapkho.ma_phieu}"
    )
def xoa_phieu_nhap(request, pk):
    phieu = get_object_or_404(NhapKho, pk=pk)
    if request.method == 'POST':
        phieu.delete()
        return redirect('inventory:nhapkho_list')
    return render(request, 'inventory/xoa_phieu_nhap.html', {'phieu': phieu})


@login_required
def danh_sach_xuat(request):
    """Danh sách xuất kho với bộ lọc đơn giản"""
    # Lấy tất cả phiếu xuất
    xuatkho_list = XuatKho.objects.select_related('kho', 'kho_nhan', 'nguoi_lap').order_by('-ngay_xuat')

    # Lấy tham số lọc
    search_query = request.GET.get('q', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Lọc theo ngày
    if start_date:
        xuatkho_list = xuatkho_list.filter(ngay_xuat__gte=start_date)

    if end_date:
        xuatkho_list = xuatkho_list.filter(ngay_xuat__lte=end_date)

    # Tìm kiếm
    if search_query:
        xuatkho_list = xuatkho_list.filter(
            Q(ma_phieu__icontains=search_query) |
            Q(kho__ten_kho__icontains=search_query) |
            Q(kho_nhan__ten_kho__icontains=search_query) |
            Q(nguoi_lap__username__icontains=search_query) |
            Q(ghi_chu__icontains=search_query)
        )

    context = {
        'xuatkho_list': xuatkho_list,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'inventory/xuatkho_list.html', context)

@login_required
def xuat_kho_create(request):
    kho_list = Kho.objects.filter(trang_thai='dang_hoat_dong')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                kho_xuat_id = request.POST.get('kho_xuat')
                kho_nhan_id = request.POST.get('kho_nhan')
                ghi_chu = request.POST.get('ghi_chu', '').strip()

                if not kho_xuat_id or not kho_nhan_id:
                    messages.error(request, "Vui lòng chọn cả kho xuất và kho nhận!")
                    return redirect('inventory:xuatkho_form')

                kho_xuat = get_object_or_404(Kho, id=kho_xuat_id)
                kho_nhan = get_object_or_404(Kho, id=kho_nhan_id)

                if kho_xuat == kho_nhan:
                    messages.error(request, "Kho xuất và kho nhận không được giống nhau!")
                    return redirect('inventory:xuatkho_form')

                # --- Lấy danh sách sản phẩm và số lượng ---
                ten_san_pham_list = request.POST.getlist('ten_san_pham')
                so_luong_list = request.POST.getlist('so_luong')

                # Vì đã xóa don_gia từ form và model, nên không cần lấy don_gia_list

                # --- Kiểm tra đầu vào ---
                if not ten_san_pham_list or not so_luong_list:
                    messages.error(request, "Vui lòng thêm ít nhất một sản phẩm!")
                    return redirect('inventory:xuatkho_form')

                # Kiểm tra xem các list có cùng độ dài không
                if len(ten_san_pham_list) != len(so_luong_list):
                    messages.error(request, "Dữ liệu sản phẩm không hợp lệ!")
                    return redirect('inventory:xuatkho_form')

                # --- Bước 1: Kiểm tra tồn kho trước ---
                for i, ten_sp in enumerate(ten_san_pham_list):
                    if not ten_sp.strip():
                        continue
                    try:
                        sp = SanPham.objects.get(ten_san_pham=ten_sp)
                        sl = int(so_luong_list[i])
                    except (ValueError, IndexError, SanPham.DoesNotExist):
                        continue

                    ton = QuanLyTonKho.kiem_tra_ton_kho(kho_xuat, sp)
                    if ton['so_luong_kha_dung'] < sl:
                        messages.error(request,
                                       f"Sản phẩm {sp.ten_san_pham} không đủ tồn kho (còn {ton['so_luong_kha_dung']})!")
                        return redirect('inventory:xuatkho_form')

                # --- Bước 2: Tạo phiếu xuất ---
                xuatkho = XuatKho.objects.create(
                    nguoi_lap=request.user,
                    kho=kho_xuat,
                    kho_nhan=kho_nhan,
                    ghi_chu=ghi_chu,
                    ngay_xuat=timezone.now()
                )

                # Sinh mã phiếu
                last = XuatKho.objects.order_by('-id').first()
                seq = (last.id + 1) if last else 1
                xuatkho.ma_phieu = f"XKNB-{seq:04d}"
                xuatkho.save()

                # --- Bước 3: Lưu chi tiết và cập nhật tồn kho ---
                for i, ten_sp in enumerate(ten_san_pham_list):
                    if not ten_sp.strip():
                        continue
                    try:
                        sp = SanPham.objects.get(ten_san_pham=ten_sp)
                        sl = int(so_luong_list[i])
                    except (ValueError, IndexError, SanPham.DoesNotExist):
                        continue

                    if sl <= 0:
                        continue

                    # Tạo chi tiết xuất KHÔNG có don_gia
                    ChiTietXuatKho.objects.create(
                        phieu_xuat=xuatkho,
                        san_pham=sp,
                        so_luong=sl

                    )

                    # Trừ kho xuất
                    try:
                        QuanLyTonKho.xuat_hang(kho_xuat, sp, sl)
                    except ValueError as e:
                        messages.error(request, str(e))
                        xuatkho.delete()  # Xóa phiếu xuất nếu có lỗi
                        return redirect('inventory:xuatkho_form')

                    # Cộng kho nhận
                    ton_nhan, created = TonKho.objects.get_or_create(kho=kho_nhan, san_pham=sp)
                    ton_nhan.so_luong_ton += sl
                    ton_nhan.so_luong_kha_dung += sl
                    ton_nhan.save()

                messages.success(request, f"Tạo phiếu xuất nội bộ {xuatkho.ma_phieu} thành công!")
                return redirect('inventory:xuatkho_list')

        except Exception as e:
            messages.error(request, f"Lỗi khi tạo phiếu xuất: {str(e)}")

    context = {
        'san_pham_list': SanPham.objects.filter(trang_thai=True),
        'danh_muc_list': DanhMucSanPham.objects.all(),
        'don_vi_tinh_list': DonViTinh.objects.all(),
        'kho_list': kho_list,
    }
    return render(request, 'inventory/xuatkho_form.html', context)


def xuat_kho_detail(request, pk):
    phieu_xuat = get_object_or_404(XuatKho, pk=pk)
    chi_tiet_list = phieu_xuat.chi_tiet_xuat.all()
    return render(request, 'inventory/xuatkho_detail.html', {
        'phieu_xuat': phieu_xuat,
        'chi_tiet_list': chi_tiet_list
    })
def xoa_phieu_xuat(request, pk):
    phieu = get_object_or_404(XuatKho, pk=pk)
    if request.method == 'POST':
        phieu.delete()
        messages.success(request, f"Phiếu xuất {phieu.ma_phieu} đã được xóa!")
        return redirect('inventory:xuatkho_list')
    return render(request, 'inventory/xoa_phieu_xuat.html', {'phieu': phieu})

#  KIỂM KÊ


@login_required
def danh_sach_kiem_ke(request):
    try:
        # Bắt đầu với tất cả kiểm kê
        danh_sach = KiemKe.objects.all().order_by('-ngay_tao')

        # Lấy các tham số lọc từ GET request
        search_query = request.GET.get('q', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        # Áp dụng bộ lọc
        if start_date:
            danh_sach = danh_sach.filter(ngay_kiem_ke__gte=start_date)

        if end_date:
            danh_sach = danh_sach.filter(ngay_kiem_ke__lte=end_date)

        if search_query:
            danh_sach = danh_sach.filter(
                Q(ma_kiem_ke__icontains=search_query) |
                Q(ten_dot_kiem_ke__icontains=search_query) |
                Q(kho__ten_kho__icontains=search_query) |
                Q(nguoi_phu_trach__username__icontains=search_query)
            )

    except OperationalError:
        danh_sach = []
        messages.error(request, 'Có lỗi database. Vui lòng chạy migrations.')

    return render(request, 'inventory/danh_sach_kiem_ke.html', {
        'danh_sach_kiem_ke': danh_sach
    })
@login_required
def tao_kiem_ke(request):
    if request.method == 'POST':
        try:
            ma_kiem_ke = request.POST.get('ma_kiem_ke')
            ten_dot_kiem_ke = request.POST.get('ten_dot_kiem_ke')
            ngay_kiem_ke = request.POST.get('ngay_kiem_ke')
            kho_id = request.POST.get('kho')
            mo_ta = request.POST.get('mo_ta', '')

            # Kiểm tra mã kiểm kê đã tồn tại chưa
            if KiemKe.objects.filter(ma_kiem_ke=ma_kiem_ke).exists():
                messages.error(request, 'Mã kiểm kê đã tồn tại! Vui lòng chọn mã khác.')
                return render(request, 'inventory/tao_kiem_ke.html')

            kho = get_object_or_404(Kho, id=kho_id)

            kiem_ke = KiemKe(
                ma_kiem_ke=ma_kiem_ke,
                ten_dot_kiem_ke=ten_dot_kiem_ke,
                ngay_kiem_ke=ngay_kiem_ke,
                kho=kho,
                mo_ta=mo_ta,
                nguoi_phu_trach=request.user
            )
            kiem_ke.save()

            messages.success(request, f'Tạo đợt kiểm kê "{ten_dot_kiem_ke}" thành công!')
            return redirect('inventory:chi_tiet_kiem_ke', id=kiem_ke.id)

        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'inventory/tao_kiem_ke.html')

    # GET request - hiển thị form
    danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong')
    return render(request, 'inventory/tao_kiem_ke.html', {'danh_sach_kho': danh_sach_kho})


@login_required
def chi_tiet_kiem_ke(request, id):
    try:
        # Đảm bảo id là số nguyên
        kiem_ke_id = int(id)
        kiem_ke = get_object_or_404(KiemKe, id=kiem_ke_id)
    except (ValueError, TypeError):
        # Nếu không phải số, thử tìm bằng mã kiểm kê
        try:
            kiem_ke = get_object_or_404(KiemKe, ma_kiem_ke=id)
        except:
            messages.error(request, 'Không tìm thấy đợt kiểm kê')
            return redirect('inventory:danh_sach_kiem_ke')

    # Kiểm tra xem kho có phải là instance của Kho không
    if not isinstance(kiem_ke.kho, Kho):
        messages.error(request, 'Dữ liệu kho không hợp lệ')
        return redirect('inventory:danh_sach_kiem_ke')

    # Lấy danh sách sản phẩm
    san_phams = SanPham.objects.all()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                for san_pham in san_phams:
                    so_luong_thuc_te_key = f'so_luong_{san_pham.id}'
                    so_luong_thuc_te = request.POST.get(so_luong_thuc_te_key)

                    if so_luong_thuc_te and so_luong_thuc_te.strip():
                        # Kiểm tra tồn kho
                        ton_kho_info = QuanLyTonKho.kiem_tra_ton_kho(kiem_ke.kho, san_pham)
                        so_luong_he_thong = ton_kho_info['so_luong_ton']
                        so_luong_thuc_te_int = int(so_luong_thuc_te)

                        # Tạo hoặc cập nhật chi tiết kiểm kê
                        chi_tiet, created = ChiTietKiemKe.objects.get_or_create(
                            kiem_ke=kiem_ke,
                            san_pham=san_pham,
                            defaults={
                                'so_luong_he_thong': so_luong_he_thong,
                                'so_luong_thuc_te': so_luong_thuc_te_int
                            }
                        )

                        if not created:
                            chi_tiet.so_luong_he_thong = so_luong_he_thong
                            chi_tiet.so_luong_thuc_te = so_luong_thuc_te_int
                            chi_tiet.save()

                kiem_ke.trang_thai = 'hoan_thanh'
                kiem_ke.save()

                messages.success(request, 'Cập nhật kiểm kê thành công!')
                return redirect('inventory:danh_sach_kiem_ke')

        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    # Chuẩn bị dữ liệu cho template
    chi_tiet_kiem_ke_list = []
    for san_pham in san_phams:
        # Kiểm tra tồn kho
        try:
            ton_kho_info = QuanLyTonKho.kiem_tra_ton_kho(kiem_ke.kho, san_pham)
            so_luong_he_thong = ton_kho_info['so_luong_ton']
        except:
            so_luong_he_thong = 0

        # Lấy chi tiết kiểm kê hiện có
        chi_tiet_existing = ChiTietKiemKe.objects.filter(
            kiem_ke=kiem_ke,
            san_pham=san_pham
        ).first()

        chi_tiet_kiem_ke_list.append({
            'san_pham': san_pham,
            'so_luong_he_thong': so_luong_he_thong,
            'so_luong_thuc_te': chi_tiet_existing.so_luong_thuc_te if chi_tiet_existing else so_luong_he_thong,
            'chenh_lech': chi_tiet_existing.chenh_lech if chi_tiet_existing else 0,
            'ghi_chu': chi_tiet_existing.ghi_chu if chi_tiet_existing else ''
        })

    context = {
        'kiem_ke': kiem_ke,
        'chi_tiet_kiem_ke_list': chi_tiet_kiem_ke_list
    }
    return render(request, 'inventory/chi_tiet_kiem_ke.html', context)

# QUẢN LÝ KHO

@login_required
def danh_sach_kho(request):
    danh_sach_kho = Kho.objects.all().order_by('ma_kho')
    return render(request, 'inventory/danh_sach_kho.html', {
        'danh_sach_kho': danh_sach_kho
    })


@login_required
def tao_kho(request):
    if request.method == 'POST':
        ma_kho = request.POST.get('ma_kho')
        ten_kho = request.POST.get('ten_kho')
        dia_chi = request.POST.get('dia_chi')
        dien_thoai = request.POST.get('dien_thoai')

        if Kho.objects.filter(ma_kho=ma_kho).exists():
            messages.error(request, 'Mã kho đã tồn tại!')
            return render(request, 'inventory/tao_kho.html')

        kho = Kho(
            ma_kho=ma_kho,
            ten_kho=ten_kho,
            dia_chi=dia_chi,
            dien_thoai=dien_thoai,
            nguoi_quan_ly=request.user
        )
        kho.save()
        messages.success(request, 'Tạo kho thành công!')
        return redirect('inventory:danh_sach_kho')

    return render(request, 'inventory/tao_kho.html')



@login_required
def chi_tiet_ton_kho(request, kho_id=None):

    print(f"=== DEBUG: View called ===")
    print(f"kho_id from URL: {kho_id}")
    print(f"GET parameters: {dict(request.GET)}")

    # Lấy danh sách kho và sản phẩm
    danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong')
    danh_sach_san_pham = SanPham.objects.all()

    # Lấy filter từ GET parameters
    kho_filter = request.GET.get('kho', '')
    san_pham_filter = request.GET.get('san_pham', '')

    # QUERY BAN ĐẦU
    ton_kho_query = TonKho.objects.all().select_related(
        'kho',
        'san_pham',
        'san_pham__danh_muc',
        'san_pham__don_vi_tinh'
    )

    # LOGIC LỌC THEO THỨ TỰ ƯU TIÊN:
    # 1. Ưu tiên filter từ form trước
    # 2. Nếu không có filter từ form, dùng kho_id từ URL
    # 3. Nếu không có gì cả, hiển thị tất cả

    if 'kho' in request.GET:  # Form đã được submit
        print("Form has been submitted")
        if kho_filter and kho_filter != '':
            # Filter theo giá trị từ form
            try:
                kho_filter_id = int(kho_filter)
                ton_kho_query = ton_kho_query.filter(kho_id=kho_filter_id)
                print(f"Filtering by form: kho_id={kho_filter_id}")
            except (ValueError, TypeError):
                print(f"Invalid form filter: {kho_filter}")
        else:
            # kho_filter = '' -> hiển thị tất cả
            print("Form kho is empty - showing ALL warehouses")
            # KHÔNG thêm filter nào
    else:
        # Không có form submission
        print("No form submission")
        if kho_id:
            # Dùng kho_id từ URL
            try:
                ton_kho_query = ton_kho_query.filter(kho_id=kho_id)
                print(f"Filtering by URL kho_id: {kho_id}")
            except (ValueError, TypeError):
                print(f"Invalid URL kho_id: {kho_id}")
        else:
            print("No kho_id in URL - showing ALL warehouses")

    # Filter sản phẩm (luôn từ form)
    if san_pham_filter and san_pham_filter != '':
        try:
            san_pham_filter_id = int(san_pham_filter)
            ton_kho_query = ton_kho_query.filter(san_pham_id=san_pham_filter_id)
            print(f"Filtering by product: {san_pham_filter_id}")
        except (ValueError, TypeError):
            print(f"Invalid product filter: {san_pham_filter}")

    # Sắp xếp
    ton_kho_query = ton_kho_query.order_by('kho__ten_kho', 'san_pham__ten_san_pham')

    # Debug: đếm số lượng
    total_records = ton_kho_query.count()
    print(f"Total records: {total_records}")

    # Đếm theo từng kho
    for kho in danh_sach_kho:
        count = ton_kho_query.filter(kho=kho).count()
        if count > 0:
            print(f"Warehouse '{kho.ten_kho}' (ID={kho.id}): {count} products")

    print("=== END DEBUG ===\n")

    # Thống kê
    total_quantity = ton_kho_query.aggregate(
        total=Sum('so_luong_ton')
    )['total'] or 0

    context = {
        'danh_sach_kho': danh_sach_kho,
        'danh_sach_san_pham': danh_sach_san_pham,
        'ton_kho': ton_kho_query,
        'selected_kho': kho_filter,
        'selected_san_pham': san_pham_filter,
        'total_quantity': total_quantity,
        'total_records': total_records,
    }

    return render(request, 'inventory/chi_tiet_ton_kho.html', context)
#  API & UTILITIES
def kiem_tra_ton_kho_api(request, kho_id, san_pham_id):
    """API kiểm tra tồn kho"""
    try:
        kho = get_object_or_404(Kho, id=kho_id)
        san_pham = get_object_or_404(SanPham, id=san_pham_id)

        ton_kho = QuanLyTonKho.kiem_tra_ton_kho(kho, san_pham)

        return JsonResponse({
            'success': True,
            'so_luong_ton': ton_kho['so_luong_ton'],
            'so_luong_kha_dung': ton_kho['so_luong_kha_dung']
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_danh_sach_kho_api(request):
    """API lấy danh sách kho"""
    try:
        danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong').values('id', 'ma_kho', 'ten_kho')
        return JsonResponse({
            'success': True,
            'danh_sach_kho': list(danh_sach_kho)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)

       })



