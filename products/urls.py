from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('units/', views.unit_list, name='unit_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('units/add/', views.unit_create, name='unit_create'),
]
