from django.db import transaction, models  # sửa: import models
from .models import TonKho


class QuanLyTonKho:
    @staticmethod
    @transaction.atomic
    def nhap_hang(kho, san_pham, so_luong):
        """Xử lý nhập hàng vào kho"""
        ton_kho, created = TonKho.objects.get_or_create(
            kho=kho,
            san_pham=san_pham,
            defaults={
                'so_luong_ton': so_luong,
                'so_luong_kha_dung': so_luong
            }
        )

        if not created:
            ton_kho.so_luong_ton += so_luong
            ton_kho.so_luong_kha_dung += so_luong
            ton_kho.save()

        return ton_kho

    @staticmethod
    @transaction.atomic
    def xuat_hang(kho, san_pham, so_luong):
        """Xử lý xuất hàng từ kho"""
        try:
            ton_kho = TonKho.objects.get(kho=kho, san_pham=san_pham)

            if ton_kho.so_luong_kha_dung < so_luong:
                raise ValueError(
                    f"Không đủ số lượng tồn kho. "
                    f"Yêu cầu: {so_luong}, Tồn kho: {ton_kho.so_luong_kha_dung}"
                )

            ton_kho.so_luong_ton -= so_luong
            ton_kho.so_luong_kha_dung -= so_luong
            ton_kho.save()

            return ton_kho

        except TonKho.DoesNotExist:
            raise ValueError(f"Sản phẩm {getattr(san_pham, 'ten_san_pham', san_pham)} không tồn tại trong kho")

    @staticmethod
    def kiem_tra_ton_kho(kho, san_pham):
        """Kiểm tra tồn kho của sản phẩm"""
        try:
            ton_kho = TonKho.objects.get(kho=kho, san_pham=san_pham)
            return {
                'so_luong_ton': ton_kho.so_luong_ton,
                'so_luong_kha_dung': ton_kho.so_luong_kha_dung
            }
        except TonKho.DoesNotExist:
            return {'so_luong_ton': 0, 'so_luong_kha_dung': 0}

    @staticmethod
    def get_tong_ton_kho(san_pham):
        """Lấy tổng tồn kho của sản phẩm across all kho"""
        tong_ton_kho = TonKho.objects.filter(san_pham=san_pham).aggregate(
            tong_ton=models.Sum('so_luong_ton'),
            tong_kha_dung=models.Sum('so_luong_kha_dung')
        )
        return {
            'tong_ton': tong_ton_kho['tong_ton'] or 0,
            'tong_kha_dung': tong_ton_kho['tong_kha_dung'] or 0
        }
