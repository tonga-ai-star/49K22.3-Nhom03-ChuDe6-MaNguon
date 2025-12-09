from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from inventory.models import NhapKho
from .models import CongNo
from django.db import transaction
import re

@receiver(post_save, sender=NhapKho)
def tao_cong_no_tu_nhap_kho(sender, instance, created, **kwargs):
    if created and instance.tong_tien>0:
        try:
            with transaction.atomiic():
                last_cong_no = CongNo.objects.select_for_update().order_by('-id').first()
            if last_cong_no and last_cong_no.ma_cong_no:
                try:
                    # Tách số từ mã công nợ cuối cùng
                    match = re.search(r'CN-?(\d+)', last_cong_no.ma_cong_no)
                    if match:
                        last_number = int(match.group(1))
                    else:
                        last_number = 0
                    new_number = last_number + 1
                except (ValueError, AttributeError):
                    new_number = 1
            else:
                new_number = 1

            # Tạo mã mới và kiểm tra trùng
            ma_cong_no_moi = f"CN-{new_number:04d}"
            counter = 1
            while CongNo.objects.filter(ma_cong_no=ma_cong_no_moi).exists():
                new_number += 1
                ma_cong_no_moi = f"CN-{new_number:04d}"
                counter += 1
                if counter > 1000:
                    ma_cong_no_moi = f"CN-{instance.id}-{timezone.now().strftime('%H%M%S')}"
                    break

            # ✅ LẤY THÔNG TIN HÀNG HÓA TỪ CHI TIẾT NHẬP
            ten_hang_hoa = "Hàng nhập kho"
            so_luong = 1

            if hasattr(instance, 'chi_tiet_nhap') and instance.chi_tiet_nhap.exists():
                chi_tiet_items = list(instance.chi_tiet_nhap.all())
                if chi_tiet_items:
                    # Lấy tên sản phẩm đầu tiên
                    first_item = chi_tiet_items[0]
                    ten_hang_hoa = first_item.san_pham.ten_san_pham if first_item.san_pham else "Hàng nhập kho"

                    # Tính tổng số lượng
                    so_luong = sum([item.so_luong for item in chi_tiet_items])

                    # Nếu có nhiều sản phẩm, thêm "..."
                    if len(chi_tiet_items) > 1:
                        ten_hang_hoa += f" và {len(chi_tiet_items) - 1} sản phẩm khác"

            # Giới hạn độ dài tên hàng hóa
            ten_hang_hoa = ten_hang_hoa[:250]

            # ✅ TẠO CÔNG NỢ
            CongNo.objects.create(
                ma_cong_no=ma_cong_no_moi,
                nha_cung_cap=instance.nha_cung_cap,
                phieu_nhap=instance,
                loai_cong_no='phai_tra',
                ten_hang_hoa=ten_hang_hoa,
                so_luong=so_luong,
                don_gia=instance.tong_tien / so_luong if so_luong > 0 else instance.tong_tien,
                so_tien=instance.tong_tien,
                so_tien_con_lai=instance.tong_tien,
                han_thanh_toan=timezone.now().date() + timedelta(days=30),
                ghi_chu=f"Công nợ từ phiếu nhập {instance.ma_phieu}"
            )

            print(f"✅ Đã tạo công nợ {ma_cong_no_moi} cho phiếu nhập {instance.ma_phieu}")

        except Exception as e:
            print(f"Lỗi khi tạo công nợ từ nhập kho: {e}")