from django.contrib import admin
from .models import NhapKho, ChiTietNhapKho, XuatKho, ChiTietXuatKho
from .models import KiemKe, ChiTietKiemKe
from .models import Kho, TonKho

class ChiTietNhapKhoInline(admin.TabularInline):
    model = ChiTietNhapKho
    extra = 1
    fields = ['san_pham', 'so_luong', 'don_gia', 'thanh_tien']
    readonly_fields = ['thanh_tien']

@admin.register(NhapKho)
class NhapKhoAdmin(admin.ModelAdmin):
    list_display = ['ma_phieu', 'kho', 'nha_cung_cap', 'nguoi_lap', 'ngay_nhap', 'trang_thai']
    list_filter = ['kho', 'nha_cung_cap', 'trang_thai']
    search_fields = ['ma_phieu', 'ghi_chu']
    inlines = [ChiTietNhapKhoInline]

class ChiTietXuatKhoInline(admin.TabularInline):
    model = ChiTietXuatKho
    extra = 1
    fields = ['san_pham', 'so_luong']


@admin.register(XuatKho)
class XuatKhoAdmin(admin.ModelAdmin):
    list_display = ['ma_phieu', 'kho', 'kho_nhan', 'nguoi_lap', 'ngay_xuat']
    list_filter = ['kho', 'kho_nhan', 'nguoi_lap']
    search_fields = ['ma_phieu', 'ghi_chu']
    inlines = [ChiTietXuatKhoInline]

@admin.register(ChiTietNhapKho)
class ChiTietNhapKhoAdmin(admin.ModelAdmin):
    list_display = ['phieu_nhap', 'san_pham', 'so_luong', 'don_gia', 'thanh_tien']
    list_filter = ['phieu_nhap', 'san_pham']

@admin.register(ChiTietXuatKho)
class ChiTietXuatKhoAdmin(admin.ModelAdmin):
    # CHỈ CÒN 3 TRƯỜNG VÌ ĐÃ XÓA don_gia và thanh_tien
    list_display = ['phieu_xuat', 'san_pham', 'so_luong']
    list_filter = ['phieu_xuat', 'san_pham']

class ChiTietKiemKeInline(admin.TabularInline):
    model = ChiTietKiemKe
    extra = 1

@admin.register(KiemKe)
class KiemKeAdmin(admin.ModelAdmin):
    list_display = ['ma_kiem_ke', 'ten_dot_kiem_ke', 'kho', 'ngay_kiem_ke', 'trang_thai', 'nguoi_phu_trach']
    list_filter = ['trang_thai', 'kho', 'ngay_kiem_ke']
    search_fields = ['ma_kiem_ke', 'ten_dot_kiem_ke']
    inlines = [ChiTietKiemKeInline]

@admin.register(ChiTietKiemKe)
class ChiTietKiemKeAdmin(admin.ModelAdmin):
    list_display = ['kiem_ke', 'san_pham', 'so_luong_he_thong', 'so_luong_thuc_te', 'chenh_lech']
    list_filter = ['kiem_ke']

@admin.register(Kho)
class KhoAdmin(admin.ModelAdmin):
    list_display = ['ma_kho', 'ten_kho', 'dia_chi', 'nguoi_quan_ly', 'trang_thai']
    list_filter = ['trang_thai']
    search_fields = ['ma_kho', 'ten_kho', 'dia_chi']
    list_editable = ['trang_thai']

@admin.register(TonKho)
class TonKhoAdmin(admin.ModelAdmin):
    list_display = ['kho', 'san_pham', 'so_luong_ton', 'so_luong_kha_dung', 'ngay_cap_nhat']
    list_filter = ['kho', 'san_pham']
    search_fields = ['kho__ten_kho', 'san_pham__ten_san_pham']