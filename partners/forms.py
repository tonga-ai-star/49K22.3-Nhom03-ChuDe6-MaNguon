from django import forms
from .models import NhaCungCap
class NhaCungCapForm(forms.ModelForm):
    class Meta:
        model = NhaCungCap
        fields = ['ma_nha_cung_cap', 'ten_nha_cung_cap', 'dia_chi', 'dien_thoai', 'email', 'ghi_chu']
        widgets = {
            'ma_nha_cung_cap': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mã nhà cung cấp'}),
            'ten_nha_cung_cap': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên nhà cung cấp'}),
            'dia_chi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Địa chỉ'}),
            'dien_thoai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ghi chú'}),
        }
