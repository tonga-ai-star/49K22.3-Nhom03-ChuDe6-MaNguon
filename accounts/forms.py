from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import NguoiDung


class NguoiDungForm(UserCreationForm):
    class Meta:
        model = NguoiDung
        fields = ['username', 'ho_ten', 'email', 'vai_tro', 'trang_thai']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tùy chỉnh widgets
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})