from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_register_view, name='register'),
    path('api/checkout/', views.pos_checkout_api, name='checkout_api'),
    path('api/products/add/', views.pos_add_product_api, name='add_product_api'),
    path('api/products/<int:product_id>/restock/', views.pos_restock_api, name='restock_api'),
    path('receipt/<str:receipt_number>/', views.pos_thermal_receipt_view, name='thermal_receipt'),
]
