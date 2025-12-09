from django.urls import path
from . import views
app_name = 'inventory'
urlpatterns = [
    # NHẬP KHO
    path('nhap-kho/', views.danh_sach_nhap, name='nhapkho_list'),
    path('nhap-kho/them/', views.nhap_kho_create, name='nhap_kho_create'),
    path('nhap-kho/<int:pk>/', views.nhap_kho_detail, name='nhap_kho_detail'),
    path('nhap-kho/<int:pk>/xoa/', views.xoa_phieu_nhap, name='xoa_phieu_nhap'),
    # XUẤT KHO
    path('xuat-kho/', views.danh_sach_xuat, name='xuatkho_list'),
    path('xuat-kho/them/', views.xuat_kho_create, name='xuatkho_form'),
    path('xuat-kho/<int:pk>/', views.xuat_kho_detail, name='xuat_kho_detail'),
    path('xuat-kho/<int:pk>/xoa/', views.xoa_phieu_xuat, name='xoa_phieu_xuat'),
    #TẠO KIỂM KÊ
    path('', views.danh_sach_kiem_ke, name='danh_sach_kiem_ke'),
    path('tao-kiem-ke/', views.tao_kiem_ke, name='tao_kiem_ke'),
    path('chi-tiet-kiem-ke/<int:id>/', views.chi_tiet_kiem_ke, name='chi_tiet_kiem_ke'),
    path('kho/', views.danh_sach_kho, name='danh_sach_kho'),
    path('kho/tao-moi/', views.tao_kho, name='tao_kho'),
    path('ton-kho/', views.chi_tiet_ton_kho, name='chi_tiet_ton_kho'),
    path('kho/<int:kho_id>/ton-kho/', views.chi_tiet_ton_kho, name='chi_tiet_ton_kho'),
]