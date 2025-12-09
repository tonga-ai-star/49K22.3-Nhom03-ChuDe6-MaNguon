from django.urls import path
from . import views

app_name = 'debt'

urlpatterns = [
    path('', views.CongNoListView.as_view(), name='congno_list'),
    path('tao-moi/', views.congno_create, name='congno_create'),
    path('<int:pk>/', views.CongNoDetailView.as_view(), name='congno_detail'),
    path('<int:pk>/thanh-toan/', views.thanh_toan_cong_no, name='thanh_toan'),
]