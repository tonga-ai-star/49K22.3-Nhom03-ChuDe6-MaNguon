
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from products.models import SanPham
from inventory.models import NhapKho, XuatKho  # ĐÃ SỬA TÊN
from partners.models import NhaCungCap
@login_required
def reports_dashboard(request):
    # Thống kê cơ bản
    total_products = SanPham.objects.count()
    total_suppliers = NhaCungCap.objects.count()

    # Thống kê tồn kho
    inventory_stats = SanPham.objects.aggregate(
        total_inventory=Sum('ton_kho'),
        avg_price=Avg('gia_ban'),
        low_stock=Count('id', filter= Q(ton_kho__lt=10))
    )

    # Thống kê nhập xuất tháng
    today = timezone.now()
    first_day = today.replace(day=1)

    monthly_import = NhapKho.objects.filter(
        ngay_tao__gte=first_day
    ).aggregate(total=Sum('tong_tien'))['total'] or 0

    monthly_export = XuatKho.objects.filter(
        ngay_tao__gte=first_day
    ).aggregate(total=Sum('tong_tien'))['total'] or 0

    # Top sản phẩm tồn kho nhiều
    top_products = SanPham.objects.order_by('-ton_kho')[:10]

    # Sản phẩm sắp hết hàng
    low_stock_products = SanPham.objects.filter(ton_kho__lt=10)

    context = {
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'inventory_stats': inventory_stats,
        'monthly_import': monthly_import,
        'monthly_export': monthly_export,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'reports/dashboard.html', context)


@login_required
def inventory_report(request):
    products = SanPham.objects.all().order_by('-ton_kho')
    return render(request, 'reports/inventory_report.html', {'products': products})


@login_required
def import_export_report(request):
    # Báo cáo nhập xuất 30 ngày gần đây
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    imports = NhapKho.objects.filter(ngay_tao__range=[start_date, end_date])
    exports = XuatKho.objects.filter(ngay_tao__range=[start_date, end_date])

    context = {
        'imports': imports,
        'exports': exports,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'reports/import_export_report.html', context)