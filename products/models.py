from django.db import models


class DanhMucSanPham(models.Model):
    ten_danh_muc = models.CharField(max_length=100)
    mo_ta = models.TextField(blank=True, null=True)
    trang_thai = models.BooleanField(default=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.ten_danh_muc
    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Danh mục sản phẩm"
class DonViTinh(models.Model):
    ten_don_vi = models.CharField(max_length=50)
    mo_ta = models.TextField(blank=True, null=True)
    trang_thai = models.BooleanField(default=True)
    def __str__(self):
        return self.ten_don_vi
    class Meta:
        verbose_name = "Đơn vị tính"
        verbose_name_plural = "Đơn vị tính"
class SanPham(models.Model):
    danh_muc = models.ForeignKey(DanhMucSanPham, on_delete=models.CASCADE)
    don_vi_tinh = models.ForeignKey(DonViTinh, on_delete=models.CASCADE)
    ma_san_pham = models.CharField(max_length=50, unique=True)
    ten_san_pham = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True, null=True)
    gia_nhap = models.DecimalField(max_digits=15, decimal_places=2)
    gia_ban = models.DecimalField(max_digits=15, decimal_places=2)
    trang_thai = models.BooleanField(default=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    so_luong_toi_thieu = models.PositiveIntegerField(
        default=10,
        verbose_name='Số lượng tối thiểu',
        help_text='Số lượng tối thiểu trong kho để cảnh báo'
    )

    def __str__(self):
        return self.ten_san_pham

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"