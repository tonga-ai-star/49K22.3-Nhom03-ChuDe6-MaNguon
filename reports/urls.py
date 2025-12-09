from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('ton-kho/', views.inventory_report, name='inventory_report'),
    path('nhap-xuat/', views.import_export_report, name='import_export_report'),
]