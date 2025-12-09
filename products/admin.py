from django.contrib import admin
from .models import DanhMucSanPham, DonViTinh, SanPham

@admin.register(DanhMucSanPham)
class DanhMucSanPhamAdmin(admin.ModelAdmin):
    list_display = ['ten_danh_muc', 'trang_thai', 'ngay_tao']

@admin.register(DonViTinh)
class DonViTinhAdmin(admin.ModelAdmin):
    list_display = ['ten_don_vi']

@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    list_display = ['ma_san_pham', 'ten_san_pham', 'danh_muc', 'gia_ban', 'trang_thai']
    list_filter = ['danh_muc', 'trang_thai']
    search_fields = ['ma_san_pham', 'ten_san_pham']