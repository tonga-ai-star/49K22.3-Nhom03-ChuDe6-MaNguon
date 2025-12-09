from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum, Count
from .models import NguoiDung
from .forms import NguoiDungForm
from django.contrib.auth.decorators import login_required
from products.models import SanPham
from inventory.models import NhapKho, XuatKho, TonKho, ChiTietNhapKho, ChiTietXuatKho
from partners.models import NhaCungCap
from django.db.models.functions import ExtractMonth
from datetime import datetime
import calendar


@login_required
def danh_sach_nhan_vien(request):
    nhan_vien_list = NguoiDung.objects.filter(vai_tro__in=['staff', 'manager'])

    # --- Lấy tham số tìm kiếm & lọc ---
    q = request.GET.get('q', '').strip()
    vai_tro = request.GET.get('vai_tro', '')
    trang_thai = request.GET.get('trang_thai', '')

    # --- Tìm kiếm ---
    if q:
        nhan_vien_list = nhan_vien_list.filter(
            Q(ho_ten__icontains=q) |
            Q(username__icontains=q) |
            Q(email__icontains=q)
        )

    # --- Lọc theo vai trò ---
    if vai_tro:
        nhan_vien_list = nhan_vien_list.filter(vai_tro=vai_tro)

    # --- Lọc theo trạng thái ---
    if trang_thai:
        nhan_vien_list = nhan_vien_list.filter(trang_thai=(trang_thai == 'true'))

    # --- Sắp xếp mới nhất ---
    nhan_vien_list = nhan_vien_list.order_by('-date_joined')

    # --- Thống kê ---
    tong_nhan_vien = nhan_vien_list.count()
    nhan_vien_dang_lam = nhan_vien_list.filter(trang_thai=True).count()
    nhan_vien_nghi_viec = nhan_vien_list.filter(trang_thai=False).count()

    # --- Gửi dữ liệu qua template ---
    context = {
        'nhan_vien_list': nhan_vien_list,
        'tong_nhan_vien': tong_nhan_vien,
        'nhan_vien_dang_lam': nhan_vien_dang_lam,
        'nhan_vien_nghi_viec': nhan_vien_nghi_viec,

        # giữ lại giá trị lọc & tìm kiếm trong form
        'search_query': q,
        'selected_vai_tro': vai_tro,
        'selected_trang_thai': trang_thai,
    }

    return render(request, 'accounts/danh_sach_nhan_vien.html', context)


@login_required
def them_nhan_vien(request):
    if request.method == 'POST':
        form = NguoiDungForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password('123456')  # Mật khẩu mặc định
            user.save()
            messages.success(request, 'Thêm nhân viên thành công!')
            return redirect('danh_sach_nhan_vien')
    else:
        form = NguoiDungForm()

    context = {
        'form': form,
        'title': 'Thêm nhân viên mới'
    }
    return render(request, 'accounts/them_nhan_vien.html', context)


@login_required
def chi_tiet_nhan_vien(request, nhan_vien_id):
    nhan_vien = get_object_or_404(NguoiDung, id=nhan_vien_id)

    context = {
        'nhan_vien': nhan_vien
    }
    return render(request, 'accounts/chi_tiet_nhan_vien.html', context)


@login_required
def sua_nhan_vien(request, nhan_vien_id):
    nhan_vien = get_object_or_404(NguoiDung, id=nhan_vien_id)

    if request.method == 'POST':
        form = NguoiDungForm(request.POST, instance=nhan_vien)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật thông tin nhân viên thành công!')
            return redirect('danh_sach_nhan_vien')
    else:
        form = NguoiDungForm(instance=nhan_vien)

    context = {
        'form': form,
        'nhan_vien': nhan_vien,
        'title': 'Sửa thông tin nhân viên'
    }
    return render(request, 'accounts/them_nhan_vien.html', context)


@login_required
def xoa_nhan_vien(request, nhan_vien_id):
    nhan_vien = get_object_or_404(NguoiDung, id=nhan_vien_id)

    if nhan_vien.id == request.user.id:
        messages.error(request, 'Không thể xóa chính tài khoản của bạn!')
    else:
        nhan_vien.delete()
        messages.success(request, 'Đã xóa nhân viên thành công!')

    return redirect('danh_sach_nhan_vien')


@login_required
def dashboard(request):
    current_year = datetime.now().year
    current_month = datetime.now().month

    # --- Xử lý bộ lọc tháng ---
    selected_month = request.GET.get('month')
    if selected_month:
        selected_month = int(selected_month)

    # --- 1. Tổng quan ---
    total_products = SanPham.objects.count()
    total_suppliers = NhaCungCap.objects.count()

    # --- 2. Tổng số phiếu nhập/xuất trong tháng (theo lọc) ---
    if selected_month:
        # Nếu có lọc theo tháng
        imports_this_month = NhapKho.objects.filter(
            ngay_nhap__month=selected_month,
            ngay_nhap__year=current_year
        ).count()

        exports_this_month = XuatKho.objects.filter(
            ngay_xuat__month=selected_month,
            ngay_xuat__year=current_year
        ).count()

        # Tổng số lượng nhập/xuất trong tháng
        total_import_quantity = ChiTietNhapKho.objects.filter(
            phieu_nhap__ngay_nhap__month=selected_month,
            phieu_nhap__ngay_nhap__year=current_year
        ).aggregate(total=Sum('so_luong'))['total'] or 0

        total_export_quantity = ChiTietXuatKho.objects.filter(
            phieu_xuat__ngay_xuat__month=selected_month,
            phieu_xuat__ngay_xuat__year=current_year
        ).aggregate(total=Sum('so_luong'))['total'] or 0
    else:
        # Nếu không lọc, lấy tháng hiện tại
        imports_this_month = NhapKho.objects.filter(
            ngay_nhap__month=current_month,
            ngay_nhap__year=current_year
        ).count()

        exports_this_month = XuatKho.objects.filter(
            ngay_xuat__month=current_month,
            ngay_xuat__year=current_year
        ).count()

        total_import_quantity = ChiTietNhapKho.objects.filter(
            phieu_nhap__ngay_nhap__month=current_month,
            phieu_nhap__ngay_nhap__year=current_year
        ).aggregate(total=Sum('so_luong'))['total'] or 0

        total_export_quantity = ChiTietXuatKho.objects.filter(
            phieu_xuat__ngay_xuat__month=current_month,
            phieu_xuat__ngay_xuat__year=current_year
        ).aggregate(total=Sum('so_luong'))['total'] or 0

    # --- 3. Top sản phẩm tồn nhiều nhất ---
    top_stock_products = (
        TonKho.objects.select_related('san_pham')
        .values('san_pham__id', 'san_pham__ten_san_pham', 'san_pham__ma_san_pham')
        .annotate(tong_ton=Sum('so_luong_ton'))
        .order_by('-tong_ton')[:5]
    )

    # --- 4. Sản phẩm sắp hết hàng - ĐÃ SỬA LỖI ---
    low_stock = []
    all_tonkho = TonKho.objects.select_related('san_pham').all()

    for tonkho in all_tonkho:
        if tonkho.san_pham:
            # Kiểm tra xem sản phẩm có trường so_luong_toi_thieu không
            so_luong_toi_thieu = getattr(tonkho.san_pham, 'so_luong_toi_thieu', 10)  # Mặc định là 10 nếu không có

            # Sản phẩm sắp hết nếu tồn kho <= 10
            if tonkho.so_luong_ton <= 10:
                # Tính phần trăm tồn kho so với mức tối thiểu
                try:
                    phan_tram = (tonkho.so_luong_ton / so_luong_toi_thieu) * 100
                except ZeroDivisionError:
                    phan_tram = 0

                low_stock.append({
                    'san_pham': tonkho.san_pham,
                    'so_luong_ton': tonkho.so_luong_ton,
                    'so_luong_toi_thieu': so_luong_toi_thieu,
                    'phan_tram_ton': round(phan_tram, 1)
                })

    # Chỉ lấy top 5 sản phẩm có tồn kho thấp nhất
    low_stock = sorted(low_stock, key=lambda x: x['so_luong_ton'])[:5]

    # --- 5. Xuất nội bộ gần đây - ĐÃ SỬA LỖI ---
    # Sửa 'nguoi_xuat' thành 'nguoi_lap'
    try:
        recent_exports = XuatKho.objects.select_related('nguoi_lap').order_by('-ngay_xuat')[:5]
    except Exception as e:
        print(f"Lỗi khi lấy recent_exports: {e}")
        recent_exports = XuatKho.objects.all().order_by('-ngay_xuat')[:5]

    # --- 6. Biểu đồ nhập kho ---
    if selected_month:
        # Nếu có lọc tháng: hiển thị theo ngày trong tháng
        days_in_month = calendar.monthrange(current_year, selected_month)[1]
        labels = [f'{i}' for i in range(1, days_in_month + 1)]

        # Lấy dữ liệu nhập theo ngày
        import_data = []
        for day in range(1, days_in_month + 1):
            total = ChiTietNhapKho.objects.filter(
                phieu_nhap__ngay_nhap__day=day,
                phieu_nhap__ngay_nhap__month=selected_month,
                phieu_nhap__ngay_nhap__year=current_year
            ).aggregate(total=Sum('so_luong'))['total'] or 0
            import_data.append(total)

        # Tính tổng nhập và trung bình ngày
        total_import_month = sum(import_data)
        avg_import_day = total_import_month / days_in_month if days_in_month > 0 else 0

        chart_title = f'Biểu đồ nhập kho tháng {selected_month}'

    else:
        # Nếu không lọc: hiển thị theo tháng trong năm
        labels = [f'Tháng {i}' for i in range(1, 13)]

        # Lấy dữ liệu nhập theo tháng
        import_data = []
        for month in range(1, 13):
            total = ChiTietNhapKho.objects.filter(
                phieu_nhap__ngay_nhap__month=month,
                phieu_nhap__ngay_nhap__year=current_year
            ).aggregate(total=Sum('so_luong'))['total'] or 0
            import_data.append(total)

        # Tính tổng và trung bình
        total_import_year = sum(import_data)
        avg_import_month = total_import_year / 12 if len(import_data) > 0 else 0

        chart_title = f'Biểu đồ nhập kho năm {current_year}'

    # --- 7. Top nhà cung cấp (để sẵn nếu cần sau này) - ĐÃ SỬA LỖI ---
    try:
        top_suppliers = (
            ChiTietNhapKho.objects.select_related('phieu_nhap__nha_cung_cap')
            .filter(phieu_nhap__nha_cung_cap__isnull=False)
            .values('phieu_nhap__nha_cung_cap__id', 'phieu_nhap__nha_cung_cap__ten_nha_cung_cap')
            .annotate(
                so_lan_nhap=Count('phieu_nhap__nha_cung_cap'),
                tong_san_pham=Sum('so_luong')
            )
            .order_by('-tong_san_pham')[:5]
        )
    except Exception as e:
        # Nếu vẫn lỗi, tạo danh sách rỗng
        print(f"Lỗi query top_suppliers: {e}")
        top_suppliers = []

    # --- 8. Danh sách tháng cho dropdown ---
    months = [
        {'value': i, 'label': f'Tháng {i}'}
        for i in range(1, 13)
    ]

    # --- 9. Tính cân đối nhập/xuất ---
    net_import = total_import_quantity - total_export_quantity

    # --- 10. Context gửi đến template ---
    context = {
        # Tổng quan
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'imports_this_month': imports_this_month,
        'exports_this_month': exports_this_month,
        'total_import_quantity': total_import_quantity,
        'total_export_quantity': total_export_quantity,
        'net_import': net_import,

        # Phân tích tồn kho
        'top_stock_products': list(top_stock_products),
        'low_stock': low_stock,
        'recent_exports': recent_exports,

        # Biểu đồ
        'labels': labels,
        'import_data': import_data,
        'chart_title': chart_title,

        # Thông tin năm/tháng
        'current_year': current_year,
        'current_month': current_month,
        'selected_month': selected_month,

        # Dropdown tháng
        'months': months,

        # Thống kê biểu đồ
        'total_import_year': total_import_year if not selected_month else 0,
        'avg_import_month': avg_import_month if not selected_month else 0,
        'total_import_month': total_import_month if selected_month else 0,
        'avg_import_day': avg_import_day if selected_month else 0,

        # Top nhà cung cấp (để dành)
        'top_suppliers': list(top_suppliers),
    }

    return render(request, 'dashboard.html', context)