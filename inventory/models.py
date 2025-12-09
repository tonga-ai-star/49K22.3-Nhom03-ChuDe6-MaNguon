from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import SanPham
from partners.models import NhaCungCap
from django.db.models import Sum
from decimal import Decimal
from django.core.exceptions import ValidationError
import re


class Kho(models.Model):
    TRANG_THAI_CHOICES = [
        ('dang_hoat_dong', 'Đang hoạt động'),
        ('ngung_hoat_dong', 'Ngừng hoạt động'),
        ('bao_tri', 'Bảo trì'),
    ]
    ma_kho = models.CharField(max_length=20, unique=True, verbose_name="Mã kho")
    ten_kho = models.CharField(max_length=100, verbose_name="Tên kho")
    dia_chi = models.TextField(verbose_name="Địa chỉ")
    nguoi_quan_ly = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Người quản lý"
    )
    dien_thoai = models.CharField(max_length=15, blank=True, verbose_name="Điện thoại")
    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='dang_hoat_dong',
        verbose_name="Trạng thái"
    )
    ghi_chu = models.TextField(blank=True, verbose_name="Ghi chú")
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kho"
        verbose_name_plural = "Kho"

    def __str__(self):
        return f"{self.ma_kho} - {self.ten_kho}"


class TonKho(models.Model):
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, verbose_name="Kho")
    san_pham = models.ForeignKey('products.SanPham', on_delete=models.CASCADE, verbose_name="Sản phẩm")
    so_luong_ton = models.IntegerField(default=0, verbose_name="Số lượng tồn")
    so_luong_kha_dung = models.IntegerField(default=0, verbose_name="Số lượng khả dụng")
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tồn kho"
        verbose_name_plural = "Tồn kho"
        unique_together = ['kho', 'san_pham']

    def __str__(self):
        return f"{self.kho.ten_kho} - {self.san_pham.ten_san_pham}: {self.so_luong_ton}"


# === NHẬP KHO ===
class NhapKho(models.Model):
    ma_phieu = models.CharField(max_length=50, unique=True)
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE)
    ngay_nhap = models.DateTimeField(auto_now_add=True)
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    nguoi_lap = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tong_tien = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # THÊM LẠI TRƯỜNG TỔNG TIỀN
    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    trang_thai = models.CharField(max_length=20, default='chưa duyệt')

    class Meta:
        verbose_name = "Phiếu nhập kho"
        verbose_name_plural = "Phiếu nhập kho"
        ordering = ['-ngay_nhap']

    def __str__(self):
        return self.ma_phieu

    def save(self, *args, **kwargs):
        if not self.ma_phieu:
            last_phieu = NhapKho.objects.order_by('-id').first()
            if last_phieu:
                match = re.search(r'(\d+)$', last_phieu.ma_phieu)
                if match:
                    last_number = int(match.group(1))
                else:
                    last_number = 0
                self.ma_phieu = f'NK-{last_number + 1:04d}'
            else:
                self.ma_phieu = 'NK-0001'
        super().save(*args, **kwargs)

    def update_tong_tien(self):
        from django.db.models import Sum
        from decimal import Decimal
        total = self.chi_tiet_nhap.aggregate(total=Sum('thanh_tien'))['total'] or Decimal('0')
        self.tong_tien = total
        self.save(update_fields=['tong_tien'])


class ChiTietNhapKho(models.Model):
    phieu_nhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE, related_name='chi_tiet_nhap')
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong = models.IntegerField(validators=[MinValueValidator(1)])
    don_gia = models.DecimalField(max_digits=15, decimal_places=2)
    thanh_tien = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Chi tiết nhập kho"
        verbose_name_plural = "Chi tiết nhập kho"

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.so_luong}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.thanh_tien = self.so_luong * self.don_gia
        super().save(*args, **kwargs)

        # Cập nhật tồn kho (TonKho)
        if is_new:
            ton, created = TonKho.objects.get_or_create(kho=self.phieu_nhap.kho, san_pham=self.san_pham)
            ton.so_luong_ton += self.so_luong
            ton.so_luong_kha_dung += self.so_luong
            ton.save()

        # Cập nhật tổng tiền phiếu nhập
        self.phieu_nhap.update_tong_tien()

    def delete(self, *args, **kwargs):
        phieu_nhap = self.phieu_nhap
        ton = TonKho.objects.filter(kho=phieu_nhap.kho, san_pham=self.san_pham).first()
        super().delete(*args, **kwargs)

        # Giảm tồn kho khi xóa chi tiết
        if ton:
            ton.so_luong_ton -= self.so_luong
            ton.so_luong_kha_dung -= self.so_luong
            ton.save()

        # Cập nhật lại tổng tiền phiếu nhập
        phieu_nhap.update_tong_tien()


# === XUẤT KHO ===
class XuatKho(models.Model):
    ma_phieu = models.CharField(max_length=50, unique=True)
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE, related_name='phieu_xuat_kho')
    kho_nhan = models.ForeignKey(Kho, on_delete=models.CASCADE, related_name='phieu_nhan_kho')
    ngay_xuat = models.DateTimeField(auto_now_add=True)
    nguoi_lap = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Phiếu xuất kho"
        verbose_name_plural = "Phiếu xuất kho"

    def __str__(self):
        return self.ma_phieu

    def save(self, *args, **kwargs):
        if not self.ma_phieu:
            last_phieu = XuatKho.objects.order_by('-id').first()
            if last_phieu:
                match = re.search(r'(\d+)$', last_phieu.ma_phieu)
                last_number = int(match.group(1)) if match else 0
                self.ma_phieu = f'XK-{last_number + 1:04d}'
            else:
                self.ma_phieu = 'XK-0001'
        super().save(*args, **kwargs)


class ChiTietXuatKho(models.Model):
    phieu_xuat = models.ForeignKey('XuatKho', on_delete=models.CASCADE, related_name='chi_tiet_xuat')
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Chi tiết xuất kho"
        verbose_name_plural = "Chi tiết xuất kho"

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.so_luong}"

    def save(self, *args, **kwargs):
        # CHỈ KIỂM TRA TỒN KHO
        ton = TonKho.objects.filter(kho=self.phieu_xuat.kho, san_pham=self.san_pham).first()

        # Kiểm tra tồn kho
        if not ton or ton.so_luong_kha_dung < self.so_luong:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f"Sản phẩm {self.san_pham.ten_san_pham} không đủ tồn kho "
                f"(còn {ton.so_luong_kha_dung if ton else 0})!"
            )

        # Lưu chi tiết xuất
        super().save(*args, **kwargs)


# === KIỂM KÊ ===
class KiemKe(models.Model):
    TRANG_THAI_CHON = [
        ('cho', 'Chờ'),
        ('dang_kiem_ke', 'Đang kiểm kê'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy'),
    ]

    ma_kiem_ke = models.CharField(max_length=50, unique=True, verbose_name="Mã kiểm kê")
    ten_dot_kiem_ke = models.CharField(max_length=200, verbose_name="Tên đợt kiểm kê")
    ngay_kiem_ke = models.DateTimeField(verbose_name="Ngày kiểm kê")
    kho = models.ForeignKey(Kho, on_delete=models.CASCADE)
    nguoi_phu_trach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Người phụ trách"
    )
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_CHON, default='cho', verbose_name="Trạng thái")
    mo_ta = models.TextField(blank=True, verbose_name="Mô tả")
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kiểm kê"
        verbose_name_plural = "Kiểm kê"

    def __str__(self):
        return f"{self.ma_kiem_ke} - {self.ten_dot_kiem_ke}"


class ChiTietKiemKe(models.Model):
    kiem_ke = models.ForeignKey(KiemKe, on_delete=models.CASCADE, related_name='chi_tiet', verbose_name="Đợt kiểm kê")
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE, verbose_name="Sản phẩm")
    so_luong_he_thong = models.IntegerField(verbose_name="Số lượng hệ thống")
    so_luong_thuc_te = models.IntegerField(verbose_name="Số lượng thực tế")
    chenh_lech = models.IntegerField(default=0, verbose_name="Chênh lệch")
    ghi_chu = models.TextField(blank=True, verbose_name="Ghi chú")

    class Meta:
        verbose_name = "Chi tiết kiểm kê"
        verbose_name_plural = "Chi tiết kiểm kê"

    def save(self, *args, **kwargs):
        self.chenh_lech = self.so_luong_thuc_te - self.so_luong_he_thong
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.chenh_lech}"