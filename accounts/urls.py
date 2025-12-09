from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('nhan-vien/', views.danh_sach_nhan_vien, name='danh_sach_nhan_vien'),
    path('nhan-vien/them/', views.them_nhan_vien, name='them_nhan_vien'),
    path('nhan-vien/<int:nhan_vien_id>/', views.chi_tiet_nhan_vien, name='chi_tiet_nhan_vien'),
    path('nhan-vien/<int:nhan_vien_id>/sua/', views.sua_nhan_vien, name='sua_nhan_vien'),
    path('nhan-vien/<int:nhan_vien_id>/xoa/', views.xoa_nhan_vien, name='xoa_nhan_vien'),
]
