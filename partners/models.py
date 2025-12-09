from django.db import models


class NhaCungCap(models.Model):
    ma_nha_cung_cap = models.CharField(max_length=50, unique=True)
    ten_nha_cung_cap = models.CharField(max_length=200)
    dia_chi = models.TextField()
    dien_thoai = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ten_nha_cung_cap

    class Meta:
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"



