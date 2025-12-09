from django.db import models
from django.conf import settings
from partners.models import NhaCungCap
from inventory.models import NhapKho
from django.utils import timezone
import random

class CongNo(models.Model):
    LOAI_CHOICES = [
        ('phai_thu', 'Phải thu'),
        ('phai_tra', 'Phải trả'),
    ]
    phieu_nhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE)
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    ma_cong_no = models.CharField(max_length=20, unique=True)
    loai_cong_no = models.CharField(max_length=10, choices=LOAI_CHOICES)
    ten_hang_hoa = models.CharField(max_length=255)
    so_luong = models.IntegerField(default=1)
    don_gia = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    so_tien = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    so_tien_con_lai = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    han_thanh_toan = models.DateField(null=True, blank=True)  # Thêm trường này
    ghi_chu = models.TextField(blank=True, null=True)  # Thêm trường này
    def __init__(self, *args, **kwargs):
        # Xử lý các trường không tồn tại
        kwargs.pop('some_unexpected_field', None)
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        # TẠO MÃ CÔNG NỢ DUY NHẤT NẾU CHƯA CÓ
        if not self.ma_cong_no:
            # Cách 1: Dùng timestamp để đảm bảo duy nhất
            timestamp = int(timezone.now().timestamp())
            random_suffix = random.randint(100, 999)
            self.ma_cong_no = f"CN-{timestamp}{random_suffix}"

            # Kiểm tra lại để đảm bảo không trùng (rất hiếm)
            while CongNo.objects.filter(ma_cong_no=self.ma_cong_no).exists():
                random_suffix = random.randint(100, 999)
                self.ma_cong_no = f"CN-{timestamp}{random_suffix}"

        # TÍNH TOÁN SỐ TIỀN
        if not self.so_tien or self.so_tien == 0:
            self.so_tien = self.so_luong * self.don_gia

        if not self.pk:  # Chỉ set khi tạo mới
            self.so_tien_con_lai = self.so_tien

        super().save(*args, **kwargs)

    def thanh_toan(self):
        """Phương thức thanh toán"""
        if self.so_tien_con_lai > 0:
            LichSuThanhToan.objects.create(
                cong_no=self,
                so_tien=self.so_tien_con_lai,
                nguoi_thanh_toan=settings.AUTH_USER_MODEL.objects.first()  # Tạm thời
            )
            self.so_tien_con_lai = 0
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.ma_cong_no} - {self.nha_cung_cap.ten}"


class LichSuThanhToan(models.Model):
    cong_no = models.ForeignKey(CongNo, on_delete=models.CASCADE, related_name='lich_su_thanh_toan')
    so_tien = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ngay_thanh_toan = models.DateTimeField(auto_now_add=True)
    nguoi_thanh_toan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Thanh toán {self.so_tien} cho {self.cong_no.ma_cong_no}"