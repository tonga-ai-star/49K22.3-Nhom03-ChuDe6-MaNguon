# products/forms.py
from django import forms
from .models import DanhMucSanPham, SanPham, DonViTinh

# Form cho thêm danh mục
class DanhMucForm(forms.ModelForm):
    class Meta:
        model = DanhMucSanPham
        fields = ['ten_danh_muc', 'mo_ta', 'trang_thai']
        widgets = {
            'ten_danh_muc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Xi măng'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Không bắt buộc'}),
            'trang_thai': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DonViTinhForm(forms.ModelForm):
    class Meta:
        model = DonViTinh
        fields = ['ten_don_vi', 'mo_ta']
        widgets = {
            'ten_don_vi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Bao'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Không bắt buộc'}),
        }

# Form cho sản phẩm (đã có, bổ sung queryset)
class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = '__all__'
        widgets = {
            'ma_san_pham': forms.TextInput(attrs={'class': 'form-control'}),
            'ten_san_pham': forms.TextInput(attrs={'class': 'form-control'}),
            'danh_muc': forms.Select(attrs={'class': 'form-select'}),
            'don_vi_tinh': forms.Select(attrs={'class': 'form-select'}),
            'gia_nhap': forms.NumberInput(attrs={'class': 'form-control'}),
            'gia_ban': forms.NumberInput(attrs={'class': 'form-control'}),
            'ton_kho': forms.NumberInput(attrs={'class': 'form-control'}),
            'trang_thai': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['danh_muc'].queryset = DanhMucSanPham.objects.all().order_by('ten_danh_muc')
        self.fields['don_vi_tinh'].queryset = DonViTinh.objects.all().order_by('ten_don_vi')