from django import forms
from products.models import SanPham
from partners.models import NhaCungCap
from django.forms import inlineformset_factory
from .models import NhapKho, XuatKho, ChiTietNhapKho, ChiTietXuatKho, Kho

class NhapKhoForm(forms.ModelForm):
    class Meta:
        model = NhapKho
        fields = ['nha_cung_cap', 'ghi_chu']
        widgets = {
            'kho': forms.Select(attrs={'class': 'form-control select2', 'id': 'kho-select'}),
            'nha_cung_cap': forms.Select(attrs={
                'class': 'form-control select2',
                'id': 'nha-cung-cap-select'
            }),
            'ghi_chu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhập ghi chú cho phiếu nhập kho...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['nha_cung_cap'].queryset = NhaCungCap.objects.all()


class ChiTietNhapKhoForm(forms.ModelForm):
    san_pham = forms.ModelChoiceField(
        queryset=SanPham.objects.filter(trang_thai=True),
        widget=forms.Select(attrs={
            'class': 'form-control san-pham-select',
            'required': 'true'
        }),
        label="Sản phẩm"
    )

    so_luong = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control so-luong-input',
            'min': '1',
            'required': 'true'
        }),
        label="Số lượng"
    )

    don_gia = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control don-gia-input',
            'step': '1000',
            'required': 'true'
        }),
        label="Đơn giá"
    )

    class Meta:
        model = ChiTietNhapKho
        fields = ['san_pham', 'so_luong', 'don_gia']
        exclude = ['thanh_tien']


# Formset cho multiple chi tiết nhập kho
ChiTietNhapKhoFormSet = inlineformset_factory(
    NhapKho,
    ChiTietNhapKho,
    form=ChiTietNhapKhoForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

class XuatKhoForm(forms.ModelForm):
    class Meta:
        model = XuatKho
        fields = ['ma_phieu', 'ghi_chu']
        widgets = {
            'ma_phieu': forms.TextInput(attrs={'class': 'form-control'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # lấy ra user, tránh lỗi
        super().__init__(*args, **kwargs)

class ChiTietXuatKhoForm(forms.ModelForm):
    class Meta:
        model = ChiTietXuatKho
        fields = ['san_pham', 'so_luong']
        widgets = {
            'san_pham': forms.Select(attrs={'class': 'form-select select2', 'style': 'width:100%'}),
            'so_luong': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),

        }

    def clean(self):
        cleaned_data = super().clean()
        san_pham = cleaned_data.get('san_pham')
        so_luong = cleaned_data.get('so_luong')

        if san_pham and so_luong:
            # Kiểm tra tồn kho tổng
            if so_luong > san_pham.ton_kho:
                raise forms.ValidationError(
                    f"Sản phẩm '{san_pham.ten_san_pham}' chỉ còn {san_pham.ton_kho} trong kho!"
                )
        return cleaned_data

ChiTietXuatKhoFormSet = inlineformset_factory(
    XuatKho,
    ChiTietXuatKho,
    form=ChiTietXuatKhoForm,
    extra=1,
    can_delete=True
)