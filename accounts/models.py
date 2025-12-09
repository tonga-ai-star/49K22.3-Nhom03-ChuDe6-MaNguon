from django.db import models
from django.contrib.auth.models import AbstractUser


class NguoiDung(AbstractUser):
    ho_ten = models.CharField(max_length=100, blank=True)
    vai_tro = models.CharField(max_length=20, choices=[
        ('admin', 'Quản trị viên'),
        ('manager', 'Quản lý'),
        ('staff', 'Nhân viên'),
    ], default='staff')
    trang_thai = models.BooleanField(default=True)

    def __str__(self):
        return self.ho_ten or self.username
