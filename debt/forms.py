from django import forms
from .models import CongNo
from partners.models import NhaCungCap
from inventory.models import NhapKho


class CongNoForm(forms.ModelForm):
    phieu_nhap = forms.ModelChoiceField(
        queryset=NhapKho.objects.all(),
        label="Phiếu nhập",
        required=True
    )
    class Meta:
        model = CongNo
        fields = ['phieu_nhap','nha_cung_cap', 'ma_cong_no', 'loai_cong_no', 'ten_hang_hoa', 'so_luong', 'don_gia']
        widgets = {
            'phieu_nhap': forms.Select(attrs={'class': 'form-control'}),
            'nha_cung_cap': forms.Select(attrs={'class': 'form-control'}),
            'ma_cong_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CN001'}),
            'loai_cong_no': forms.Select(attrs={'class': 'form-control'}),
            'ten_hang_hoa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên hàng hóa'}),
            'so_luong': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'don_gia': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nha_cung_cap'].queryset = NhaCungCap.objects.all()