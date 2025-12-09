from django.contrib import admin
from .models import NhaCungCap

@admin.register(NhaCungCap)
class NhaCungCapAdmin(admin.ModelAdmin):
    list_display = ['ma_nha_cung_cap', 'ten_nha_cung_cap', 'dien_thoai', 'email']
    search_fields = ['ma_nha_cung_cap', 'ten_nha_cung_cap']

