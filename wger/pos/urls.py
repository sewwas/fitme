from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_register_view, name='register'),
    path('api/checkout/', views.pos_checkout_api, name='checkout_api'),
    path('api/products/add/', views.pos_add_product_api, name='add_product_api'),
    path('api/products/<int:product_id>/restock/', views.pos_restock_api, name='restock_api'),
    path('api/products/<int:product_id>/delete/', views.pos_delete_product_api, name='delete_product_api'),
    path('api/audit/stock/', views.pos_stock_audit_api, name='stock_audit_api'),
    path('api/audit/full/', views.pos_full_stock_audit_api, name='full_stock_audit_api'),
    path('api/audit/drawer/', views.pos_cash_drawer_audit_api, name='cash_drawer_audit_api'),
    path('api/audit/data/', views.pos_audit_data_api, name='audit_data_api'),
    path('audit/plan/', views.pos_audit_plan_view, name='audit_plan_print'),
    path('receipt/<str:receipt_number>/', views.pos_thermal_receipt_view, name='thermal_receipt'),
]
